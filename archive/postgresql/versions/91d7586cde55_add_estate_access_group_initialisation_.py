"""Add estate access group initialisation trigger

Revision ID: 91d7586cde55
Revises: 64e952bfe062
Create Date: 2025-02-18 11:04:25.008656

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91d7586cde55'
down_revision: Union[str, None] = '64e952bfe062'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create a function to create an access group for new estates.
    op.execute("""
        CREATE OR REPLACE FUNCTION create_access_group_for_estate()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO access_groups (estate_id, name)
            VALUES (NEW.id, 'REGULAR');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create a trigger that fires after an estate is inserted.
    op.execute("""
        CREATE TRIGGER create_access_group_trigger
        AFTER INSERT ON estates
        FOR EACH ROW
        EXECUTE PROCEDURE create_access_group_for_estate();
    """)

def downgrade() -> None:
    # Drop the trigger.
    op.execute("DROP TRIGGER IF EXISTS create_access_group_trigger ON estates;")
    # Drop the trigger function.
    op.execute("DROP FUNCTION IF EXISTS create_access_group_for_estate();")
