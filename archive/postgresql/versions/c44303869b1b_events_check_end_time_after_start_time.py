"""events check end_time after start_time

Revision ID: c44303869b1b
Revises: a0685f6127d6
Create Date: 2026-08-28 12:30:00.000000

Phase 3b of the hardening plan.

Adds CHECK (end_time > start_time) to `events`, created NOT VALID.

NOT VALID means existing rows are NOT scanned or rejected when the constraint is
created -- so this migration cannot fail on legacy data and touches no row. The
constraint is enforced immediately for every INSERT and for any UPDATE that
writes an events row.

Follow-up (separate migration, after the audit): once
    SELECT id FROM events WHERE end_time <= start_time;
returns nothing, run
    ALTER TABLE events VALIDATE CONSTRAINT ck_events_end_after_start;
to also guarantee it for the historical rows.

Data safety: verified on a seeded clone. A pre-existing violating row was left
in place and untouched; a new INSERT that violated the rule was rejected; the
full-table content digest was unchanged by this migration.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c44303869b1b'
down_revision: Union[str, None] = 'a0685f6127d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE events ADD CONSTRAINT ck_events_end_after_start "
        "CHECK (end_time > start_time) NOT VALID"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE events DROP CONSTRAINT IF EXISTS ck_events_end_after_start")
