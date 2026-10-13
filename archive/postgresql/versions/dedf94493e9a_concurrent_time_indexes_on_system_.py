"""concurrent time indexes on system_metrics

Revision ID: dedf94493e9a
Revises: 5911a3ade6d6
Create Date: 2026-08-28 11:54:01.500000

Phase 2b of the hardening plan.

`system_metrics` is the fastest-growing table (per-gate telemetry) and had only
its FK index. Time-range queries on device_timestamp / received_at table-scan.
Same CONCURRENTLY + autocommit_block pattern and caveats as the accesslog
revision.

Data safety: index builds read existing rows, never modify them. Verified on a
seeded clone: content hashes unchanged; both indexes valid after upgrade.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'dedf94493e9a'
down_revision: Union[str, None] = '5911a3ade6d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CREATE = [
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_system_metrics_device_timestamp "
    "ON system_metrics (device_timestamp)",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_system_metrics_received_at "
    "ON system_metrics (received_at)",
]
DROP = [
    "DROP INDEX CONCURRENTLY IF EXISTS ix_system_metrics_received_at",
    "DROP INDEX CONCURRENTLY IF EXISTS ix_system_metrics_device_timestamp",
]


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for stmt in CREATE:
            op.execute(stmt)


def downgrade() -> None:
    with op.get_context().autocommit_block():
        for stmt in DROP:
            op.execute(stmt)
