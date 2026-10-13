"""timestamptz conversion high volume tables

Revision ID: 3e96ee3d7ba6
Revises: 4306c5f30c6d
Create Date: 2026-08-28 12:30:06.000000

Phase 5b of the hardening plan.

Same conversion as 4306c5f30c6d, for the four high-write tables held back so the
lock can be scheduled: accesslog, logs, system_metrics, event_registers.

*** RUN THIS IN A MAINTENANCE WINDOW. ***
Each ALTER COLUMN TYPE takes ACCESS EXCLUSIVE on its table and fully rewrites it
plus its indexes. Size the window from the audited row counts
(SELECT relname, n_live_tup FROM pg_stat_user_tables). If the estimate is
unacceptable, replace this migration with the add-column / backfill-in-batches /
swap approach before deploying.

Conversion semantics and data safety: identical to 4306c5f30c6d -- Africa/Accra
is UTC+0 / no DST, instants unchanged, downgrade is the exact inverse. Verified
on a seeded clone with the same value-by-value equality check and downgrade
round-trip.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '3e96ee3d7ba6'
down_revision: Union[str, None] = '4306c5f30c6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ZONE = "Africa/Accra"

COLUMNS = [
    ("event_registers", "date_created"),
    ("logs", "date_created"),
    ("accesslog", "timestamp"),
    ("system_metrics", "device_timestamp"),
    ("system_metrics", "received_at"),
    ("system_metrics", "camera_alert_ts"),
]


def _convert(to_tz: bool) -> None:
    target = "timestamptz" if to_tz else "timestamp"
    for table, column in COLUMNS:
        op.execute(
            f'ALTER TABLE "{table}" ALTER COLUMN "{column}" '
            f'TYPE {target} USING "{column}" AT TIME ZONE \'{ZONE}\''
        )


def upgrade() -> None:
    _convert(to_tz=True)


def downgrade() -> None:
    _convert(to_tz=False)
