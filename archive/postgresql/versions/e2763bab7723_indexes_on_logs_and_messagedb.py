"""indexes on logs and messagedb

Revision ID: e2763bab7723
Revises: 67472e00844c
Create Date: 2026-08-28 11:53:59.900000

Phase 1b of the hardening plan.

`logs` is an audit table almost always queried by time and/or type; `messagedb`
by topic. Neither had a usable index for those access paths. Plain CREATE INDEX
is used because these tables are low-volume. If `logs` is already large in a
given environment, switch this to the CONCURRENTLY pattern used by the
accesslog / system_metrics revisions before deploying there.

Data safety: index builds read existing rows but never modify them. Verified on
a seeded clone: all table content hashes unchanged; new indexes present.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e2763bab7723'
down_revision: Union[str, None] = '67472e00844c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEXES = [
    ("ix_logs_estate_id_date_created", "logs", ["estate_id", "date_created"]),
    ("ix_logs_type", "logs", ["type"]),
    ("ix_logs_date_created", "logs", ["date_created"]),
    ("ix_messagedb_topic", "messagedb", ["topic"]),
    ("ix_messagedb_date_created", "messagedb", ["date_created"]),
]


def upgrade() -> None:
    for name, table, cols in INDEXES:
        op.create_index(name, table, cols)


def downgrade() -> None:
    for name, table, _cols in reversed(INDEXES):
        op.drop_index(name, table_name=table)
