"""pin system_metrics numeric precision

Revision ID: 80651478bdd9
Revises: 2047cc35125e
Create Date: 2026-09-01 12:00:00.000000

Review finding #20: the `Numeric` columns on `system_metrics` had no precision or
scale, so the database validated nothing (a sensor glitch could store an
absurd value).

Confirmed against production: the largest scale in use is 3 decimal places
(e.g. `23.145`), so scale = 3 rounds nothing. Precision is set generously per
column so no in-range value can overflow:

  * temperature_celsius  numeric(6, 3)   -- +/- 999.999 C
  * storage_used_gb      numeric(12, 3)  -- up to ~1 EB
  * storage_total_gb     numeric(12, 3)

A pre-flight check raises a clear error if any stored value would not fit,
rather than letting ALTER COLUMN TYPE fail with a bare "numeric field
overflow".

*** RUN IN A MAINTENANCE WINDOW. *** `system_metrics` is a high-write table and
each ALTER COLUMN TYPE takes ACCESS EXCLUSIVE and rewrites the table. If
convenient, apply this together with 3e96ee3d7ba6 (the TIMESTAMPTZ rewrite of
the same table) so the table is rewritten once.

Data safety: no value with <= 3 decimal places is changed. Verified on a seeded
clone with 3-decimal test rows -- values identical before and after; downgrade
(back to unconstrained `numeric`) is lossless. One cosmetic effect: a value like
`41.75` now renders as `41.750` (fixed scale) -- numerically identical, but a
client doing string comparison on the rendered number would see trailing zeros.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '80651478bdd9'
down_revision: Union[str, None] = '2047cc35125e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# column -> (precision, scale)
COLUMNS = {
    "temperature_celsius": (6, 3),
    "storage_used_gb": (12, 3),
    "storage_total_gb": (12, 3),
}


def upgrade() -> None:
    conn = op.get_bind()
    for column, (precision, scale) in COLUMNS.items():
        max_int_digits = precision - scale
        bad = conn.execute(sa.text(f"""
            SELECT count(*) FROM system_metrics
            WHERE {column} IS NOT NULL
              AND (abs(trunc({column})) >= :limit OR scale({column}) > :scale)
        """), {"limit": 10 ** max_int_digits, "scale": scale}).scalar()
        if bad:
            raise RuntimeError(
                f"system_metrics.{column}: {bad} row(s) will not fit "
                f"numeric({precision},{scale}). Widen the target type or clean "
                f"the data first. No changes were made."
            )

    for column, (precision, scale) in COLUMNS.items():
        op.alter_column(
            "system_metrics", column,
            type_=sa.Numeric(precision=precision, scale=scale),
            existing_nullable=False,
        )


def downgrade() -> None:
    for column in COLUMNS:
        op.alter_column(
            "system_metrics", column,
            type_=sa.Numeric(),
            existing_nullable=False,
        )
