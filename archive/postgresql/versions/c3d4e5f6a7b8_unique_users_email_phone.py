"""unique constraint on users email and phone_number

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-11 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Both columns are nullable login identifiers with no uniqueness guarantee
# today, so two different users could otherwise share the same email or
# phone number. Postgres validates existing data before applying either
# constraint and refuses (without altering anything) if a duplicate exists.
def upgrade() -> None:
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.create_unique_constraint("uq_users_phone_number", "users", ["phone_number"])


def downgrade() -> None:
    op.drop_constraint("uq_users_phone_number", "users", type_="unique")
    op.drop_constraint("uq_users_email", "users", type_="unique")
