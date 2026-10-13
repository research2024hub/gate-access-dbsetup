"""users check at least one identifier

Revision ID: 10a06d666f6e
Revises: c44303869b1b
Create Date: 2026-08-28 12:30:01.000000

Phase 3c of the hardening plan.

Adds CHECK (email IS NOT NULL OR phone_number IS NOT NULL) to `users`, created
NOT VALID. A user row with no login identifier at all is meaningless; this stops
new ones being created.

NOT VALID: existing rows are not scanned at creation time, so the migration
cannot fail on legacy data and touches no row. Enforced immediately for every
INSERT and for any UPDATE that writes a users row -- note that an UPDATE to a
pre-existing all-NULL row will now be rejected until it gets an identifier.

Follow-up (after audit): once
    SELECT id FROM users WHERE email IS NULL AND phone_number IS NULL;
returns nothing, run
    ALTER TABLE users VALIDATE CONSTRAINT ck_users_has_identifier;

Data safety: verified on a seeded clone. The seed includes users with only an
email, only a phone, and (as a deliberate legacy case) neither; all rows were
left untouched, a new all-NULL INSERT was rejected, content digest unchanged.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '10a06d666f6e'
down_revision: Union[str, None] = 'c44303869b1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT ck_users_has_identifier "
        "CHECK (email IS NOT NULL OR phone_number IS NOT NULL) NOT VALID"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_has_identifier")
