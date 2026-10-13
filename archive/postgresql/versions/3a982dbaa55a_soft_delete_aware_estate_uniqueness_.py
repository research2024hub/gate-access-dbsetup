"""soft delete aware estate uniqueness trigger

Revision ID: 3a982dbaa55a
Revises: 0715f96ac00a
Create Date: 2026-08-31 10:00:02.000000

Teaches `enforce_unique_user_per_estate` about soft deletes:

  * a soft-deleted account_holder (`deleted_at IS NOT NULL`) no longer counts
    toward the one-account-per-user-per-estate rule, so a user who left an
    estate can re-join it;
  * writing/keeping a row that is itself soft-deleted is never blocked.

Everything else is byte-for-byte the version from a0685f6127d6 (advisory lock
retained). Downgrade restores that version exactly.

Data safety: CREATE OR REPLACE FUNCTION only -- no table read or written.
Verified on a seeded clone: re-joining an estate after soft-deleting the prior
membership now succeeds; a live duplicate is still rejected; content digest
unchanged.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '3a982dbaa55a'
down_revision: Union[str, None] = '0715f96ac00a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


WITH_SOFT_DELETE = """
CREATE OR REPLACE FUNCTION enforce_unique_user_per_estate()
RETURNS TRIGGER AS $$
        DECLARE
            existing_count INTEGER;
            target_estate_id INTEGER;
        BEGIN
            -- A row that is itself soft-deleted never conflicts with anything.
            IF NEW.deleted_at IS NOT NULL THEN
                RETURN NEW;
            END IF;

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

                -- Serialize concurrent inserts for the same (user, estate) so the
                -- count-then-insert below cannot be raced.
                PERFORM pg_advisory_xact_lock(NEW.user_id, target_estate_id);

                -- Check if user already has a LIVE account in this estate
                SELECT COUNT(*) INTO existing_count
                FROM account_holders ah
                JOIN personal_info pi ON ah.personal_info_id = pi.id
                WHERE ah.user_id = NEW.user_id
                AND pi.estate_id = target_estate_id
                AND ah.deleted_at IS NULL
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
"""

WITHOUT_SOFT_DELETE = """
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

                -- Serialize concurrent inserts for the same (user, estate) so the
                -- count-then-insert below cannot be raced.
                PERFORM pg_advisory_xact_lock(NEW.user_id, target_estate_id);

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
"""


def upgrade() -> None:
    op.execute(WITH_SOFT_DELETE)


def downgrade() -> None:
    op.execute(WITHOUT_SOFT_DELETE)
