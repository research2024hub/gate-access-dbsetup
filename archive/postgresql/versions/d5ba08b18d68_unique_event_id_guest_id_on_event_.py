"""unique event_id guest_id on event_registers

Revision ID: d5ba08b18d68
Revises: 10a06d666f6e
Create Date: 2026-08-28 12:30:02.000000

Phase 3a of the hardening plan (review priority #2).

Adds UNIQUE (event_id, guest_id) to `event_registers` so the same guest cannot
be registered to the same event more than once (each duplicate also inflates the
capacity trigger's count).

This migration does NOT delete anything. If duplicates already exist it aborts
with the offending pairs listed and does nothing else. Deduplication is a
reviewed, explicit step the operator runs first:

    psql "$DATABASE_URL" -f alembic/sql/dedup_event_registers.sql

(that script keeps the earliest row per pair by id and deletes the rest), then
this migration is re-run.

The unique index is built CONCURRENTLY so ongoing writes are not blocked, then
promoted to a constraint in place (cheap, no re-scan).

Data safety: verified on a seeded clone both ways -- with a duplicate present it
aborted and changed nothing; after running the dedup script it applied and the
non-duplicate rows were byte-identical before and after.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5ba08b18d68'
down_revision: Union[str, None] = '10a06d666f6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "uq_event_registers_event_guest"


def upgrade() -> None:
    conn = op.get_bind()
    dupes = conn.execute(sa.text("""
        SELECT event_id, guest_id, count(*) AS n
        FROM event_registers
        GROUP BY event_id, guest_id
        HAVING count(*) > 1
        ORDER BY n DESC
    """)).fetchall()
    if dupes:
        sample = ", ".join(f"(event={e}, guest={g})x{n}" for e, g, n in dupes[:10])
        raise RuntimeError(
            f"event_registers has {len(dupes)} duplicated (event_id, guest_id) pair(s) "
            f"[{sample}{', ...' if len(dupes) > 10 else ''}]. "
            "Run alembic/sql/dedup_event_registers.sql first, then re-run this migration. "
            "No changes were made."
        )

    with op.get_context().autocommit_block():
        op.execute(
            f"CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS {INDEX_NAME} "
            "ON event_registers (event_id, guest_id)"
        )
    op.execute(
        f"ALTER TABLE event_registers ADD CONSTRAINT {INDEX_NAME} "
        f"UNIQUE USING INDEX {INDEX_NAME}"
    )


def downgrade() -> None:
    op.execute(f"ALTER TABLE event_registers DROP CONSTRAINT IF EXISTS {INDEX_NAME}")
    with op.get_context().autocommit_block():
        op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {INDEX_NAME}")
