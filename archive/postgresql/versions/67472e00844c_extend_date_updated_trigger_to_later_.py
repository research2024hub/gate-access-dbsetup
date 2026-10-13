"""extend date_updated trigger to later tables

Revision ID: 67472e00844c
Revises: d4e5f6a7b8c9
Create Date: 2026-08-28 11:53:58.965801

Phase 1a of the hardening plan.

The set_date_updated() function and its BEFORE UPDATE triggers were created in
11f328ef1746 for the original 14 tables. Six tables added in later migrations
carry a `date_updated` column but never got the trigger, so their value never
changes after insert. This adds the missing triggers only.

Data safety: triggers fire on future UPDATEs only. No existing row is read or
written by this migration. Verified against a seeded clone: all 25 table
content hashes unchanged after upgrade.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '67472e00844c'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tables that have a `date_updated` column but were created after the trigger
# loop in 11f328ef1746 and so were never wired to set_date_updated().
MISSING_TRIGGER_TABLES = [
    "pending_users",
    "pending_account_holders",
    "personal_info_gate_links",
    "personal_info_privilege_links",
    "user_reports",
    "report_status",
]


def upgrade() -> None:
    for table_name in MISSING_TRIGGER_TABLES:
        op.execute(f"""
            CREATE TRIGGER {table_name}_date_updated_trigger
            BEFORE UPDATE ON {table_name}
            FOR EACH ROW
            EXECUTE PROCEDURE set_date_updated();
        """)


def downgrade() -> None:
    for table_name in MISSING_TRIGGER_TABLES:
        op.execute(
            f"DROP TRIGGER IF EXISTS {table_name}_date_updated_trigger ON {table_name};"
        )
