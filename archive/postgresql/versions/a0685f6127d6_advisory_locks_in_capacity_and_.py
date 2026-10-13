"""advisory locks in capacity and uniqueness triggers

Revision ID: a0685f6127d6
Revises: dedf94493e9a
Create Date: 2026-08-28 11:54:02.000000

Phase 6 of the hardening plan.

`enforce_max_attendees` and `enforce_unique_user_per_estate` both do
SELECT COUNT(...) then allow the write, so two concurrent transactions can each
pass the check and both commit, producing the very state the trigger exists to
prevent.

This adds a single pg_advisory_xact_lock() call to each function, keyed on the
value being guarded (event id; user id + estate id). Concurrent writes for the
*same* key now serialize; writes for different keys are unaffected. The lock is
released automatically at end of transaction.

This is the low-cost mitigation. The full fix for the per-estate rule is to
denormalize estate_id onto account_holders and back it with a partial unique
index -- a separate, audit-gated change.

Data safety: CREATE OR REPLACE FUNCTION only. No table is read or written. The
function bodies are otherwise byte-for-byte the originals from 6a1206c61682 and
f1a2b3c4d5e6. Verified on a seeded clone: content hashes unchanged; a concurrent
double-registration test that previously exceeded the cap now correctly rejects
the second writer.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a0685f6127d6'
down_revision: Union[str, None] = 'dedf94493e9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MAX_ATTENDEES_WITH_LOCK = """
CREATE OR REPLACE FUNCTION enforce_max_attendees()
RETURNS TRIGGER AS $$
    DECLARE
        attendee_count INTEGER;
        attendee_limit INTEGER;
    BEGIN
        -- Serialize concurrent registrations for the same event so the
        -- count-then-insert below cannot be raced.
        PERFORM pg_advisory_xact_lock(NEW.event_id);

        SELECT COUNT(*) INTO attendee_count
        FROM event_registers
        WHERE event_id = NEW.event_id;

        SELECT max_num_of_attendees INTO attendee_limit
        FROM events
        WHERE id = NEW.event_id;

        IF attendee_limit IS NOT NULL AND attendee_count >= attendee_limit THEN
            RAISE EXCEPTION 'Cannot register guest: event has reached its maximum number of attendees (%).', attendee_limit;
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
"""

MAX_ATTENDEES_ORIGINAL = """
CREATE OR REPLACE FUNCTION enforce_max_attendees()
RETURNS TRIGGER AS $$
    DECLARE
        attendee_count INTEGER;
        attendee_limit INTEGER;
    BEGIN
        SELECT COUNT(*) INTO attendee_count
        FROM event_registers
        WHERE event_id = NEW.event_id;

        SELECT max_num_of_attendees INTO attendee_limit
        FROM events
        WHERE id = NEW.event_id;

        IF attendee_limit IS NOT NULL AND attendee_count >= attendee_limit THEN
            RAISE EXCEPTION 'Cannot register guest: event has reached its maximum number of attendees (%).', attendee_limit;
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
"""

UNIQUE_USER_ESTATE_WITH_LOCK = """
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

UNIQUE_USER_ESTATE_ORIGINAL = """
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
"""


def upgrade() -> None:
    op.execute(MAX_ATTENDEES_WITH_LOCK)
    op.execute(UNIQUE_USER_ESTATE_WITH_LOCK)


def downgrade() -> None:
    op.execute(MAX_ATTENDEES_ORIGINAL)
    op.execute(UNIQUE_USER_ESTATE_ORIGINAL)
