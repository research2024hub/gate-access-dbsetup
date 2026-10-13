"""owner_account_holder_id fk set null on delete

Revision ID: bc3a5a003434
Revises: e2763bab7723
Create Date: 2026-08-28 11:54:00.100000

Phase 1c of the hardening plan.

`account_holders.owner_account_holder_id` and
`pending_account_holders.owner_account_holder_id` are self / cross references to
account_holders with ondelete=CASCADE. Deleting a parent account holder today
silently deletes the entire sub-account chain beneath it. Both columns are
already nullable, so SET NULL is a safe swap: the child rows survive, detached.

The constraint names are discovered by introspection rather than hardcoded
(they differ: `account_holder_owner_account_holder_id_fkey` vs
`pending_account_holders_owner_account_holder_id_fkey`).

Data safety: only the FK action metadata changes. No existing row is read or
written. Verified on a seeded clone: content hashes unchanged; confdeltype
flips c -> n on upgrade and n -> c on downgrade.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc3a5a003434'
down_revision: Union[str, None] = 'e2763bab7723'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TARGETS = ["account_holders", "pending_account_holders"]
FK_COLUMN = "owner_account_holder_id"


def _swap_ondelete(new_ondelete: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table in TARGETS:
        for fk in inspector.get_foreign_keys(table):
            if fk["constrained_columns"] == [FK_COLUMN]:
                op.drop_constraint(fk["name"], table, type_="foreignkey")
                op.create_foreign_key(
                    fk["name"],
                    table,
                    fk["referred_table"],
                    fk["constrained_columns"],
                    fk["referred_columns"],
                    ondelete=new_ondelete,
                )


def upgrade() -> None:
    _swap_ondelete("SET NULL")


def downgrade() -> None:
    _swap_ondelete("CASCADE")
