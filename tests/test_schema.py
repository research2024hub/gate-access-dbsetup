import importlib.util
import os
os.environ.setdefault("DATABASE_URL", "mysql+pymysql://test:test@127.0.0.1/gate_access_test")
import unittest
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from sqlalchemy.dialects.mysql import dialect
from sqlalchemy.schema import CreateTable, CreateIndex
from app.db.database import Base
from app.db.types import UTCDateTime
import app.db.models
from scripts.schema_rules import trigger_statements
from scripts.transfer_postgres import canonical


class SchemaTests(unittest.TestCase):
    def test_frozen_migration_matches_models(self):
        path = Path('alembic/versions/mysql_0001_initial.py')
        spec = importlib.util.spec_from_file_location('baseline', path)
        baseline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(baseline)
        statements = []
        for table in Base.metadata.sorted_tables:
            statements.append(str(CreateTable(table).compile(dialect=dialect())).strip())
            for index in sorted(table.indexes, key=lambda x: x.name):
                statements.append(str(CreateIndex(index).compile(dialect=dialect())))
        def normalize(statement):
            # SQLAlchemy emits equivalent MySQL table options in hash-dependent order.
            if statement.startswith('CREATE TABLE'):
                body, options = statement.rsplit(')', 1)
                options = ' '.join(sorted(re.split(r' (?=ENGINE=|CHARSET=|COLLATE )', options)))
                return body + ')' + options
            return statement
        # mysql_0003 adds a dependency and a column to messagedb. Its live
        # migration/constraints are covered by the MySQL integration test.
        def unchanged(ddl):
            return not ddl.startswith('CREATE TABLE messagedb') and ' ON messagedb ' not in ddl
        self.assertEqual(sorted(normalize(s) for s in statements if unchanged(s)),
                         sorted(normalize(s) for s in baseline.DDL if unchanged(s)))
        repair = __import__('runpy').run_path('alembic/versions/mysql_0002_fix_trigger_locking.py')
        expected = dict(baseline.TRIGGERS)
        expected.update(repair['NEW_TRIGGERS'])
        self.assertEqual(dict(trigger_statements(Base.metadata.sorted_tables)), expected)
        self.assertEqual(25, len(Base.metadata.tables))

    def test_message_gate_model(self):
        table = Base.metadata.tables['messagedb']
        self.assertEqual({'id', 'gate_id', 'topic', 'message', 'date_created'}, set(table.c.keys()))
        self.assertTrue(table.c.gate_id.nullable)
        self.assertEqual({('gates.id', 'SET NULL')},
                         {(f.target_fullname, f.ondelete) for f in table.c.gate_id.foreign_keys})

    def test_original_user_and_membership_columns(self):
        self.assertEqual(set(Base.metadata.tables['users'].c.keys()), {
            'id', 'email', 'phone_number', 'password', 'reset_otp', 'reset_expiry',
            'is_active', 'is_admin', 'date_created', 'date_updated', 'deleted_at',
        })
        self.assertEqual(set(Base.metadata.tables['account_holders'].c.keys()), {
            'id', 'user_id', 'personal_info_id', 'house_address', 'otp',
            'otp_generated_at', 'owner_account_holder_id', 'is_active',
            'date_created', 'date_updated', 'deleted_at',
        })

    def test_guest_owner_and_report_status_constraints(self):
        guest = Base.metadata.tables['guests']
        self.assertEqual({'account_holders.id'},
                         {fk.target_fullname for fk in guest.c.creator_id.foreign_keys})
        from sqlalchemy import UniqueConstraint
        status = Base.metadata.tables['report_status']
        self.assertTrue(any(isinstance(c, UniqueConstraint) and list(c.columns.keys()) == ['report_id']
                            for c in status.constraints))

    def test_utc_conversion(self):
        original = datetime(2026, 1, 1, 12, 0, 0, 123456,
                            tzinfo=timezone(timedelta(hours=3)))
        stored = UTCDateTime().process_bind_param(original, dialect())
        self.assertEqual(datetime(2026, 1, 1, 9, 0, 0, 123456), stored)
        self.assertEqual(timezone.utc, UTCDateTime().process_result_value(stored, dialect()).tzinfo)
        self.assertEqual(canonical(original), canonical(stored))

    def test_audit_records_survive_parent_deletion(self):
        self.assertEqual({'SET NULL'}, {fk.ondelete for fk in Base.metadata.tables['logs'].foreign_keys})

if __name__ == '__main__':
    unittest.main()
