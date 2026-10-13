"""unique constraint on pending_users phone_number and pending_account_holders email

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-11 00:15:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Same gap as the users table: these are nullable identifiers with no
# uniqueness guarantee. Postgres validates existing data before applying
# either constraint and refuses (without altering anything) if a duplicate
# already exists.
def upgrade() -> None:
    op.create_unique_constraint("uq_pending_users_phone_number", "pending_users", ["phone_number"])
    op.create_unique_constraint("uq_pending_account_holders_email", "pending_account_holders", ["email"])


def downgrade() -> None:
    op.drop_constraint("uq_pending_account_holders_email", "pending_account_holders", type_="unique")
    op.drop_constraint("uq_pending_users_phone_number", "pending_users", type_="unique")
