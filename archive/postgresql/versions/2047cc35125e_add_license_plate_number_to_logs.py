"""add license_plate_number to logs

Revision ID: 2047cc35125e
Revises: 3a982dbaa55a
Create Date: 2026-09-01 10:30:00.000000

Vehicle entry/exit events (`person_arrives_with_vehicle_callback` in the gate
Lambda) should record which plate triggered them, so the audit log can be
searched by plate.

`license_plate_number` is added nullable with no server default -- existing log
rows keep NULL, the add is catalog-only (no table rewrite). The index is
partial (`WHERE license_plate_number IS NOT NULL`) because only a small fraction
of log rows are vehicle events; it still serves `WHERE license_plate_number = ?`
lookups.

Data safety: nullable column + index build. No existing row is read or written.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2047cc35125e'
down_revision: Union[str, None] = '3a982dbaa55a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "logs",
        sa.Column("license_plate_number", sa.String(20), nullable=True),
    )
    op.create_index(
        "ix_logs_license_plate_number",
        "logs",
        ["license_plate_number"],
        postgresql_where=sa.text("license_plate_number IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_logs_license_plate_number", table_name="logs")
    op.drop_column("logs", "license_plate_number")
