"""index on vehicles license_plate_number

Revision ID: 0f4a80daedb7
Revises: d5ba08b18d68
Create Date: 2026-08-28 12:30:03.000000

Phase 7 of the hardening plan.

`vehicles` is looked up by plate at the gate but had no index on
`license_plate_number`. This adds a plain (non-unique) btree index.

Uniqueness per estate is deliberately NOT added here: the review flags it as
"almost certainly yes" but it needs the audit to confirm no legitimate
cross-estate plate sharing exists, and `vehicles` has no estate_id column of its
own (it would join through personal_info). Left for a later audit-gated change.

Data safety: index build reads existing rows, never modifies them. Verified on a
seeded clone: content digest unchanged, index present.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0f4a80daedb7'
down_revision: Union[str, None] = 'd5ba08b18d68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_vehicles_license_plate_number", "vehicles", ["license_plate_number"]
    )


def downgrade() -> None:
    op.drop_index("ix_vehicles_license_plate_number", table_name="vehicles")
