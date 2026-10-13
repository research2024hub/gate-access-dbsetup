"""widen otp columns for hashed storage

Revision ID: e231770546e7
Revises: 0f4a80daedb7
Create Date: 2026-08-28 12:30:04.000000

Phase 4 of the hardening plan -- the schema half only.

The review wants OTP / reset tokens stored hashed rather than in plaintext. The
hashing itself lives in the application (this repo is schema-only), but the
columns are String(20), too short for a bcrypt/argon2 digest. This widens them
to String(255) so the app can switch to hashed writes without a further
migration.

What this migration deliberately does NOT do:
  * It does not touch or null any existing OTP value. Invalidating outstanding
    plaintext OTPs is a one-line operational step to run alongside the app
    deploy (they expire within minutes regardless):
        UPDATE users               SET reset_otp = NULL, reset_expiry = NULL   WHERE reset_otp IS NOT NULL;
        UPDATE account_holders     SET otp = NULL, otp_generated_at = NULL     WHERE otp IS NOT NULL;
        UPDATE pending_users       SET otp = NULL                              WHERE otp IS NOT NULL;
        UPDATE pending_account_holders SET otp = NULL, otp_generated_at = NULL WHERE otp IS NOT NULL;
  * It does not address pending_users.password: that column is already
    String(255); whether it is plaintext is an application question.

Data safety: widening a varchar is a catalog-only change -- no table rewrite, no
row read. Verified on a seeded clone: content digest unchanged.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e231770546e7'
down_revision: Union[str, None] = '0f4a80daedb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUMNS = [
    ("users", "reset_otp"),
    ("account_holders", "otp"),
    ("pending_users", "otp"),
    ("pending_account_holders", "otp"),
]


def upgrade() -> None:
    for table, column in COLUMNS:
        op.alter_column(table, column, type_=sa.String(255), existing_nullable=None)


def downgrade() -> None:
    # Will error if a value longer than 20 chars is present (i.e. after the app
    # started writing hashes). That is intentional: do not narrow a column that
    # now holds digests.
    for table, column in reversed(COLUMNS):
        op.alter_column(table, column, type_=sa.String(20), existing_nullable=None)
