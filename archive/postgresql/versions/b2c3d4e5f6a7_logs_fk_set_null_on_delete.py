"""logs fk set null on delete instead of cascade

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-11 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Deleting a user/estate/account-holder should not silently wipe out the
# audit trail that references them, so these FKs go from CASCADE to SET NULL.
TARGET_COLUMNS = {"estate_id", "target_account_holder_id", "actor_user_id"}


def _swap_ondelete(new_ondelete: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for fk in inspector.get_foreign_keys("logs"):
        if set(fk["constrained_columns"]) & TARGET_COLUMNS:
            op.drop_constraint(fk["name"], "logs", type_="foreignkey")
            op.create_foreign_key(
                fk["name"],
                "logs",
                fk["referred_table"],
                fk["constrained_columns"],
                fk["referred_columns"],
                ondelete=new_ondelete,
            )


def upgrade() -> None:
    _swap_ondelete("SET NULL")


def downgrade() -> None:
    _swap_ondelete("CASCADE")
