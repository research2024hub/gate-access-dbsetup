"""reset database timezone pin to utc

Revision ID: f64ae7ce01ae
Revises: 3e96ee3d7ba6
Create Date: 2026-08-28 12:30:07.000000

Phase 5c of the hardening plan (review cross-cutting issues #1 and #3).

11f328ef1746 ran `ALTER DATABASE gate_access SET timezone TO 'Africa/Accra'` --
a hardcoded database name (breaks any deploy under another name) and a
correctness crutch that is no longer needed now that every timestamp column is
timestamptz (5a/5b). This resets the per-database setting to UTC using
current_database() instead of a literal name.

`ALTER DATABASE ... SET` only affects sessions opened after it runs; existing
connections keep their current setting until they reconnect. It changes no data
and no stored value -- timestamptz values are absolute; the session timezone
only affects how they are displayed/parsed.

Run 5a and 5b first. The application should already handle display-timezone
conversion before this lands.

Data safety: verified on a seeded clone -- content digest unchanged; new
sessions report `SHOW timezone` = UTC, existing timestamptz values read back
identically.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f64ae7ce01ae'
down_revision: Union[str, None] = '3e96ee3d7ba6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _set_timezone(zone: str) -> None:
    op.execute(
        "DO $$ BEGIN "
        f"EXECUTE format('ALTER DATABASE %I SET timezone TO %L', current_database(), '{zone}'); "
        "END $$;"
    )


def upgrade() -> None:
    _set_timezone("UTC")


def downgrade() -> None:
    _set_timezone("Africa/Accra")
