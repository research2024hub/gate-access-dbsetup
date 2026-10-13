"""add initial account_types, privileges, and links per new requirements

Revision ID: 64e952bfe062
Revises: 11f328ef1746
Create Date: 2025-02-17 09:50:54.436865

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64e952bfe062'
down_revision: Union[str, None] = '11f328ef1746'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Insert initial account types: ADMIN, USER_A, GUEST, and USER_B.
    op.execute("""
        INSERT INTO account_types (name)
        VALUES ('ADMIN'), ('USER_A'), ('GUEST'), ('WORKER')
    """)

    # Insert initial privileges.
    op.execute("""
        INSERT INTO privileges (name)
        VALUES 
          ('MANAGE_ALL'),
          ('MANAGE_EVENTS'),
          ('CREATE_EVENTS'),
          ('MANAGE_GUESTS'),
          ('MANAGE_GATES'),
          ('CREATE_GUESTS'),
          ('MANAGE_ACCOUNTS'),
          ('MANAGE_ACCESS'),
          ('MANAGE_FACES'),
          ('MANAGE_DEVICES'),
          ('CREATE_VEHICLES'),
          ('VIEW_LOGS')
    """)

    # Link privileges to account types.
    # ADMIN gets only MANAGE_ALL.
    op.execute("""
        INSERT INTO account_type_privilege_links (account_type_id, privilege_id)
        VALUES
            (
              (SELECT id FROM account_types WHERE name='ADMIN'),
              (SELECT id FROM privileges WHERE name='MANAGE_ALL')
            )
    """)

    # USER_A gets MANAGE_EVENTS and MANAGE_GUESTS.
    op.execute("""
        INSERT INTO account_type_privilege_links (account_type_id, privilege_id)
        VALUES
            (
              (SELECT id FROM account_types WHERE name='USER_A'),
              (SELECT id FROM privileges WHERE name='CREATE_EVENTS')
            ),
            (
              (SELECT id FROM account_types WHERE name='USER_A'),
              (SELECT id FROM privileges WHERE name='CREATE_GUESTS')
            ),
            (
              (SELECT id FROM account_types WHERE name='USER_A'),
              (SELECT id FROM privileges WHERE name='CREATE_VEHICLES')
            )
    """)

    # TABLET gets MANAGE_FACES.
    # op.execute("""
    #     INSERT INTO account_type_privilege_links (account_type_id, privilege_id)
    #     VALUES
    #         (
    #           (SELECT id FROM account_types WHERE name='TABLET'),
    #           (SELECT id FROM privileges WHERE name='MANAGE_FACES')
    #         )
    # """)

def downgrade() -> None:
    # Remove the inserted privilege links.
    op.execute("""
        DELETE FROM account_type_privilege_links
        WHERE account_type_id IN (
            SELECT id FROM account_types WHERE name IN ('ADMIN', 'USER_A', 'GUEST', 'WORKER')
        )
          AND privilege_id IN (
            SELECT id FROM privileges WHERE name IN 
                ('MANAGE_ALL', 'MANAGE_EVENTS', 'MANAGE_ACCOUNTS', 'MANAGE_ACCESS', 'VIEW_LOGS', 'CREATE_GUESTS', 'CREATE_EVENTS', 'MANAGE_GUESTS', 'MANAGE_FACES', 'MANAGE_DEVICES')
        )
    """)
    # Remove the inserted privileges.
    op.execute("""
        DELETE FROM privileges
        WHERE name IN ('MANAGE_ALL', 'MANAGE_EVENTS', 'MANAGE_ACCOUNTS', 'MANAGE_ACCESS', 'VIEW_LOGS', 'CREATE_GUESTS', 'CREATE_EVENTS', 'MANAGE_GUESTS', 'MANAGE_FACES', 'MANAGE_DEVICES')
    """)
    # Remove the inserted account types.
    op.execute("""
        DELETE FROM account_types
        WHERE name IN ('ADMIN', 'USER_A', 'GUEST', 'WORKER')
    """)

