"""concurrent indexes on accesslog

Revision ID: 5911a3ade6d6
Revises: 41ebb658353c
Create Date: 2026-08-28 11:54:01.000000

Phase 2a of the hardening plan.

`accesslog` is a high-write table with only its FK index. Queries by plate and
by time currently table-scan. Indexes are built CONCURRENTLY so ongoing writes
are not blocked; this requires running outside a transaction, hence the
autocommit_block().

Operational notes:
  * A failed CONCURRENTLY build leaves an INVALID index behind. Recovery is to
    drop it and re-run this migration, never REINDEX inside a transaction.
  * IF NOT EXISTS / IF EXISTS make the migration re-runnable after such a
    failure.

Data safety: index builds read existing rows, never modify them. Verified on a
seeded clone: content hashes unchanged; both indexes valid after upgrade.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '5911a3ade6d6'
down_revision: Union[str, None] = '41ebb658353c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CREATE = [
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_accesslog_timestamp "
    "ON accesslog (timestamp)",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_accesslog_plate_timestamp "
    "ON accesslog (license_plate_number, timestamp)",
]
DROP = [
    "DROP INDEX CONCURRENTLY IF EXISTS ix_accesslog_plate_timestamp",
    "DROP INDEX CONCURRENTLY IF EXISTS ix_accesslog_timestamp",
]


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for stmt in CREATE:
            op.execute(stmt)


def downgrade() -> None:
    with op.get_context().autocommit_block():
        for stmt in DROP:
            op.execute(stmt)
