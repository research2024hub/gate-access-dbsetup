"""max attendees trigger enforcer added

Revision ID: 6a1206c61682
Revises: ee7e92f78675
Create Date: 2025-05-08 11:07:20.038653

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a1206c61682'
down_revision: Union[str, None] = 'ee7e92f78675'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create the trigger function
    op.execute("""
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
    """)

    # 2. Attach the trigger to the event_registers table
    op.execute("""
    CREATE TRIGGER enforce_max_attendees_trigger
    BEFORE INSERT ON event_registers
    FOR EACH ROW
    EXECUTE FUNCTION enforce_max_attendees();
    """)

def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS enforce_max_attendees_trigger ON event_registers;")
    op.execute("DROP FUNCTION IF EXISTS enforce_max_attendees;")
