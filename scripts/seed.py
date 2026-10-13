"""Seed a NEW installation only. Do not run before PostgreSQL transfer."""
from sqlalchemy import select
from app.db.database import Base, engine
import app.db.models  # noqa: F401


def main():
    tables = Base.metadata.tables
    with engine.begin() as connection:
        for name in tables:
            if connection.execute(select(tables[name]).limit(1)).first():
                raise RuntimeError('Seed requires empty application tables. Existing data will not be changed.')
        connection.execute(tables['account_types'].insert(), [
            {'id': i, 'name': name} for i, name in enumerate(['ADMIN', 'USER_A', 'GUEST', 'WORKER'], 1)])
        privileges = ['MANAGE_ALL', 'MANAGE_EVENTS', 'CREATE_EVENTS', 'MANAGE_GUESTS',
                      'MANAGE_GATES', 'CREATE_GUESTS', 'MANAGE_ACCOUNTS', 'MANAGE_ACCESS',
                      'MANAGE_FACES', 'MANAGE_DEVICES', 'CREATE_VEHICLES', 'VIEW_LOGS']
        connection.execute(tables['privileges'].insert(), [
            {'id': i, 'name': name} for i, name in enumerate(privileges, 1)])
        connection.execute(tables['account_type_privilege_links'].insert(), [
            {'account_type_id': account, 'privilege_id': privilege}
            for account, privilege in [(1, 1), (2, 3), (2, 6), (2, 11)]])
    print('Initial account types and privileges created.')

if __name__ == '__main__':
    main()
