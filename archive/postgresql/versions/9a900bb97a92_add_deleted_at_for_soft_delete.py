"""add deleted_at for soft delete

Revision ID: 9a900bb97a92
Revises: f64ae7ce01ae
Create Date: 2026-08-31 10:00:00.000000

Soft-delete support for the two "account" tables.

The rest of the schema keeps its ON DELETE CASCADE FKs untouched: because the
application stops issuing hard DELETEs against `users` / `account_holders`, the
cascades never fire and every dependent row (account_holders, events, guests,
faces, event_registers, user_reports, report_status, ...) is retained
automatically and stays referentially consistent.

`deleted_at` is distinct from the existing `is_active` flag:
  * is_active  -> account temporarily suspended / disabled, can be re-enabled
  * deleted_at -> account removed; NULL means live, a timestamp means gone

Application contract after this lands:
  * "delete account"  ->  UPDATE ... SET deleted_at = now()  (never DELETE)
  * every read filters  WHERE deleted_at IS NULL  (use a view or a default scope)

Data safety: adding a nullable column with no default is a catalog-only change
in PostgreSQL 11+ -- no table rewrite, no row touched. Verified on a seeded
clone: content digest unchanged.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a900bb97a92'
down_revision: Union[str, None] = 'f64ae7ce01ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ["users", "account_holders"]


def upgrade() -> None:
    for table in TABLES:
        op.add_column(
            table,
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        # Partial index for the "list soft-deleted" / audit path; the common
        # "WHERE deleted_at IS NULL" filter is served by the partial unique
        # indexes and existing indexes, so no plain index is added for it.
        op.create_index(
            f"ix_{table}_deleted_at",
            table,
            ["deleted_at"],
            postgresql_where=sa.text("deleted_at IS NOT NULL"),
        )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_index(f"ix_{table}_deleted_at", table_name=table)
        op.drop_column(table, "deleted_at")
