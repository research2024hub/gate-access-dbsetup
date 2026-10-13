"""add unique user estate trigger

Revision ID: f1a2b3c4d5e6
Revises: 78f7703f8804
Create Date: 2025-01-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '78f7703f8804'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create a trigger function to enforce unique user per estate constraint
    op.execute("""
        CREATE OR REPLACE FUNCTION enforce_unique_user_per_estate()
        RETURNS TRIGGER AS $$
        DECLARE
            existing_count INTEGER;
            target_estate_id INTEGER;
        BEGIN
            -- Only check if personal_info_id is provided
            IF NEW.personal_info_id IS NOT NULL THEN
                -- Get the estate_id for this account holder
                SELECT estate_id INTO target_estate_id
                FROM personal_info
                WHERE id = NEW.personal_info_id;

                -- If we couldn't find the personal_info record, let the FK constraint handle it
                IF target_estate_id IS NULL THEN
                    RETURN NEW;
                END IF;

                -- Check if user already has an account in this estate
                SELECT COUNT(*) INTO existing_count
                FROM account_holders ah
                JOIN personal_info pi ON ah.personal_info_id = pi.id
                WHERE ah.user_id = NEW.user_id
                AND pi.estate_id = target_estate_id
                AND ah.id != COALESCE(NEW.id, -1);  -- Exclude current record for updates

                -- If user already has an account in this estate, prevent the operation
                IF existing_count > 0 THEN
                    RAISE EXCEPTION 'User with ID % already has an account in estate with ID %. Only one account per user per estate is allowed.',
                        NEW.user_id, target_estate_id
                        USING ERRCODE = '23505';  -- unique_violation error code
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create the trigger that fires before INSERT or UPDATE
    op.execute("""
        CREATE TRIGGER enforce_unique_user_per_estate_trigger
        BEFORE INSERT OR UPDATE ON account_holders
        FOR EACH ROW
        EXECUTE PROCEDURE enforce_unique_user_per_estate();
    """)


def downgrade() -> None:
    # Drop the trigger
    op.execute("DROP TRIGGER IF EXISTS enforce_unique_user_per_estate_trigger ON account_holders;")

    # Drop the trigger function
    op.execute("DROP FUNCTION IF EXISTS enforce_unique_user_per_estate();")
