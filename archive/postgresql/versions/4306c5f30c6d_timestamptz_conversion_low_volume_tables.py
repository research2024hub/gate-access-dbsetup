"""timestamptz conversion low volume tables

Revision ID: 4306c5f30c6d
Revises: e231770546e7
Create Date: 2026-08-28 12:30:05.000000

Phase 5a of the hardening plan (review cross-cutting issue #1 -- "the single
biggest portability/correctness improvement available").

Converts every `timestamp without time zone` column on the lower-volume tables
to `timestamptz`. The high-write tables (accesslog, logs, system_metrics,
event_registers) are handled separately in 3e96ee3d7ba6 so their lock/rewrite
can be scheduled into a window.

Conversion semantics: the database currently runs with `timezone =
Africa/Accra` (set in 11f328ef1746) and the naive values are Accra wall-clock.
`col AT TIME ZONE 'Africa/Accra'` reinterprets each naive value as an Accra
local time and yields the correct absolute instant. Africa/Accra is UTC+0 with
no DST, so the stored instants are unchanged -- only the column type gains a
zone. The downgrade is the exact inverse.

Operational note: each ALTER COLUMN TYPE takes ACCESS EXCLUSIVE on its table and
rewrites it. These tables are small, but still deploy off-peak. Dependent
indexes are rebuilt automatically.

Data safety: verified on a seeded clone -- every affected column compared
value-by-value before and after via
    (old_naive AT TIME ZONE 'Africa/Accra') = new_timestamptz
for all rows: all equal. Round-tripped through downgrade back to identical naive
values; full content digest restored.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '4306c5f30c6d'
down_revision: Union[str, None] = 'e231770546e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ZONE = "Africa/Accra"

# Every timestamp-without-tz column on the lower-volume tables.
COLUMNS = [
    ("access_groups", "date_created"), ("access_groups", "date_updated"),
    ("account_holders", "date_created"), ("account_holders", "date_updated"),
    ("account_holders", "otp_generated_at"),
    ("account_type_privilege_links", "date_created"),
    ("account_type_privilege_links", "date_updated"),
    ("account_types", "date_created"), ("account_types", "date_updated"),
    ("estates", "date_created"), ("estates", "date_updated"),
    ("events", "date_created"), ("events", "date_updated"),
    ("events", "start_time"), ("events", "end_time"),
    ("faces", "date_created"), ("faces", "date_updated"),
    ("gate_access_group_links", "date_created"),
    ("gate_access_group_links", "date_updated"),
    ("gates", "date_created"), ("gates", "date_updated"),
    ("gates", "last_alert_sent_at"), ("gates", "last_controller_heartbeat"),
    ("guests", "date_created"), ("guests", "date_updated"),
    ("messagedb", "date_created"),
    ("pending_account_holders", "date_created"),
    ("pending_account_holders", "date_updated"),
    ("pending_account_holders", "otp_generated_at"),
    ("pending_users", "date_created"), ("pending_users", "date_updated"),
    ("pending_users", "otp_expiry"),
    ("personal_info", "date_created"), ("personal_info", "date_updated"),
    ("personal_info", "expiry"),
    ("personal_info_gate_links", "date_created"),
    ("personal_info_gate_links", "date_updated"),
    ("personal_info_privilege_links", "date_created"),
    ("personal_info_privilege_links", "date_updated"),
    ("privileges", "date_created"), ("privileges", "date_updated"),
    ("report_status", "date_created"), ("report_status", "date_updated"),
    ("user_reports", "date_created"), ("user_reports", "date_updated"),
    ("users", "date_created"), ("users", "date_updated"), ("users", "reset_expiry"),
    ("vehicles", "date_created"), ("vehicles", "date_updated"),
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
