"""Copy a read-only PostgreSQL snapshot into an empty, migrated MySQL database.

Run with --check first. Stop application writes before the final --copy.
The source is never changed. The target must be kept offline until success.
"""
import argparse
import hashlib
import json
import os
from datetime import date, datetime, time, timezone
from decimal import Decimal
from sqlalchemy import MetaData, create_engine, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import Base, engine
import app.db.models  # noqa: F401
from scripts.schema_rules import trigger_statements
from scripts.transfer_ownership import check_source_relationships, remap_guest


def canonical(value):
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value.isoformat(timespec='microseconds')
    if isinstance(value, time):
        return value.isoformat(timespec='microseconds')
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value.normalize())
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical(v) for v in value]
    return value


def digest(connection, table, names, transform=None):
    query = select(*(table.c[n] for n in names if n in table.c)).order_by(*table.primary_key.columns)
    result = connection.execution_options(stream_results=True).execute(query)
    count, checksum = 0, hashlib.sha256()
    for row in result.mappings():
        values = transform(row) if transform else row
        checksum.update(json.dumps(canonical([values[n] for n in names]), sort_keys=True,
                                   separators=(',', ':'), ensure_ascii=False).encode())
        checksum.update(b'\n')
        count += 1
    result.close()
    return count, checksum.hexdigest()


def legacy_message(row):
    """Preserve legacy messages without inventing a gate or broadcast scope."""
    return dict(row, gate_id=None)


def restore_triggers(connection):
    for name, ddl in trigger_statements(Base.metadata.sorted_tables):
        connection.exec_driver_sql(f'DROP TRIGGER IF EXISTS `{name}`')
        connection.exec_driver_sql(ddl)
    connection.commit()


def transfer(copy=False, guest_owner_overrides=None):
    source_url = make_url(os.environ['SOURCE_DATABASE_URL'])
    if source_url.get_backend_name() != 'postgresql':
        raise ValueError('SOURCE_DATABASE_URL must point to PostgreSQL.')
    source_engine = create_engine(source_url, isolation_level='REPEATABLE READ',
                                  connect_args={'options': '-c timezone=utc -c default_transaction_read_only=on'})
    with source_engine.connect() as source, engine.connect() as destination:
        source.exec_driver_sql('SET TRANSACTION READ ONLY')
        source_meta = MetaData()
        source_meta.reflect(source)
        expected = set(Base.metadata.tables)
        extras = set(source_meta.tables) - expected - {'alembic_version'}
        missing = expected - set(source_meta.tables)
        if extras or missing:
            raise ValueError(f'Source table mismatch. Extra: {sorted(extras)}; missing: {sorted(missing)}')
        destination_tables = set(inspect(destination).get_table_names())
        if destination_tables != expected | {'alembic_version'}:
            raise ValueError('Target must contain only the empty MySQL baseline; run alembic upgrade head first.')
        if destination.scalar(text('SELECT version_num FROM alembic_version')) != 'mysql_0003':
            raise ValueError('Transfer requires mysql_0003; run alembic upgrade head on the empty target first.')
        duplicate_memberships = source.scalar(text("""
            SELECT COUNT(*) FROM (
                SELECT ah.user_id, pi.estate_id
                FROM account_holders ah JOIN personal_info pi ON pi.id=ah.personal_info_id
                WHERE ah.deleted_at IS NULL
                GROUP BY ah.user_id, pi.estate_id HAVING COUNT(*) > 1
            ) AS duplicate_groups
        """))
        if duplicate_memberships:
            raise ValueError('Source contains duplicate active user/estate memberships; reconcile before copying.')
        guest_owners = check_source_relationships(source, source_meta, guest_owner_overrides)
        def transform_guest(row):
            return remap_guest(row, guest_owners)
        plan = []
        for table in Base.metadata.sorted_tables:
            original = source_meta.tables[table.name]
            names = [c.name for c in table.c if not c.computed]
            old_message = table.name == 'messagedb' and set(original.c.keys()) == set(names) - {'gate_id'}
            if set(original.c.keys()) != set(names) and not old_message:
                raise ValueError(f'{table.name}: source columns differ from the expected schema; reconcile before copying.')
            if destination.execute(select(table).limit(1)).first() is not None:
                raise ValueError(f'Target table {table.name} is not empty; refusing to overwrite data.')
            transform = transform_guest if table.name == 'guests' else None
            if old_message:
                transform = legacy_message
            count, checksum = digest(source, original, names, transform)
            plan.append((table, original, names, count, checksum))
            print(f'{table.name}: {count} source rows')
        destination.rollback()
        if not copy:
            print('Preflight passed. No records copied. Stop source writes, then rerun with --copy.')
            return
        # MySQL DDL auto-commits. Keep the target offline throughout this operation.
        # Dropping triggers avoids auto-created access groups changing preserved IDs.
        try:
            for name, _ in trigger_statements(Base.metadata.sorted_tables):
                destination.exec_driver_sql(f'DROP TRIGGER IF EXISTS `{name}`')
            destination.commit()
            with destination.begin():
                for table, original, names, _, _ in plan:
                    result = source.execution_options(stream_results=True).execute(
                        select(*(original.c[n] for n in names if n in original.c)).order_by(*original.primary_key.columns))
                    for batch in result.mappings().partitions(500):
                        rows = [dict(row) for row in batch]
                        if table.name == 'guests':
                            rows = [transform_guest(row) for row in rows]
                        if table.name == 'messagedb' and 'gate_id' not in original.c:
                            rows = [legacy_message(row) for row in rows]
                        if table.name == 'account_holders':
                            for row in rows:
                                row['owner_account_holder_id'] = None
                        destination.execute(table.insert(), rows)
                    result.close()
                # All parent IDs now exist, including self-referencing owners.
                ah = source_meta.tables['account_holders']
                for row in source.execute(select(ah.c.id, ah.c.owner_account_holder_id)):
                    if row.owner_account_holder_id is not None:
                        destination.execute(text('UPDATE account_holders SET owner_account_holder_id=:owner WHERE id=:id'),
                                            {'owner': row.owner_account_holder_id, 'id': row.id})
                for table, _, names, count, checksum in plan:
                    actual = digest(destination, table, names)
                    if actual != (count, checksum):
                        raise ValueError(f'Verification failed for {table.name}; target copy will roll back.')
                    print(f'{table.name}: count and content checksum verified')
            print('All records committed; restoring database triggers.')
        finally:
            destination.rollback()
            restore_triggers(destination)
        print('Transfer complete. Source unchanged. Review the target before switching applications.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--copy', action='store_true')
    mode.add_argument('--restore-triggers', action='store_true',
                      help='Recover trigger definitions after an interrupted copy; keep target offline.')
    parser.add_argument('--guest-owner-map', help='JSON object mapping legacy guest IDs to account-holder IDs for ambiguous owners')
    args = parser.parse_args()
    try:
        if args.restore_triggers:
            with engine.connect() as connection:
                restore_triggers(connection)
        else:
            overrides = None
            if args.guest_owner_map:
                with open(args.guest_owner_map) as file:
                    raw = json.load(file)
                if not isinstance(raw, dict) or any(type(v) is not int for v in raw.values()):
                    raise ValueError('Guest owner map must be an object of guest IDs to integer account-holder IDs.')
                overrides = {int(k): v for k, v in raw.items()}
            transfer(copy=args.copy, guest_owner_overrides=overrides)
    except SQLAlchemyError as exc:
        # SQLAlchemy exception strings can contain row values (password hashes/PII).
        print(f'Database operation failed ({type(exc).__name__}). No source data was changed.')
        raise SystemExit(1) from None
