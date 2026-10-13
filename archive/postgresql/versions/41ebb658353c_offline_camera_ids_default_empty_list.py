"""offline_camera_ids default empty list

Revision ID: 41ebb658353c
Revises: bc3a5a003434
Create Date: 2026-08-28 11:54:00.500000

Phase 1d of the hardening plan.

`system_metrics.offline_camera_ids` semantically holds a list of camera ids but
its server default is '{}'::jsonb (an empty *object*). This changes the default
to '[]'::jsonb for future inserts.

It deliberately does NOT rewrite existing rows. Any backfill of stored '{}'
values to '[]' must ship together with the application change that reads the
column as an array, and is tracked separately in the plan. `running_services`
is left alone: confirm during the audit whether it is a list or a map before
touching it.

Data safety: ALTER COLUMN ... SET DEFAULT is catalog-only and instant. No
existing row is read or written. Verified on a seeded clone: content hashes
unchanged; default flips.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '41ebb658353c'
down_revision: Union[str, None] = 'bc3a5a003434'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "system_metrics",
        "offline_camera_ids",
        server_default=sa.text("'[]'::jsonb"),
    )


def downgrade() -> None:
    op.alter_column(
        "system_metrics",
        "offline_camera_ids",
        server_default=sa.text("'{}'::jsonb"),
    )
