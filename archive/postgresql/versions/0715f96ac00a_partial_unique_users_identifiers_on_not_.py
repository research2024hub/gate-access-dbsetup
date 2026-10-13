"""partial unique users identifiers on not deleted

Revision ID: 0715f96ac00a
Revises: 9a900bb97a92
Create Date: 2026-08-31 10:00:01.000000

Makes the `users.email` / `users.phone_number` uniqueness ignore soft-deleted
rows, so a person can re-register with the same email/phone after their account
was soft-deleted.

Replaces the two full UNIQUE constraints with partial UNIQUE indexes of the
same name, `WHERE deleted_at IS NULL`. Done in a single transaction so there is
never a moment with no uniqueness guarantee.

No rows are soft-deleted yet, so the partial index covers exactly the same rows
the old constraint did -- it cannot fail on existing data (the old constraint
already guaranteed it). `users` is small enough that the in-transaction index
build locks writes only briefly; if it has grown large in some environment,
switch to the CREATE UNIQUE INDEX CONCURRENTLY form (build new, drop old,
rename) before deploying there.

Nothing has a foreign key onto `users.email` / `users.phone_number`, so the
constraint -> index change has no downstream effect.

Data safety: verified on a seeded clone -- a second live user with a duplicate
email is still rejected; after soft-deleting a user, a new user can take the
freed email/phone; content digest unchanged.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0715f96ac00a'
down_revision: Union[str, None] = '9a900bb97a92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ACTIVE = sa.text("deleted_at IS NULL")
COLUMNS = [("uq_users_email", "email"), ("uq_users_phone_number", "phone_number")]


def upgrade() -> None:
    for name, column in COLUMNS:
        op.drop_constraint(name, "users", type_="unique")
        op.create_index(name, "users", [column], unique=True, postgresql_where=ACTIVE)


def downgrade() -> None:
    for name, column in reversed(COLUMNS):
        op.drop_index(name, table_name="users")
        op.create_unique_constraint(name, "users", [column])
