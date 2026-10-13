"""Associate messages with their gate without guessing legacy ownership."""
from alembic import op
import sqlalchemy as sa

revision = "mysql_0003"
down_revision = "mysql_0002"
branch_labels = None
depends_on = None


def upgrade():
    # One ALTER minimizes the possibility of partially applied MySQL DDL.
    op.execute(sa.text("""
        ALTER TABLE messagedb
        ADD COLUMN gate_id INTEGER NULL,
        ADD INDEX ix_messagedb_gate_id (gate_id),
        ADD CONSTRAINT fk_messagedb_gate_id_gates
            FOREIGN KEY (gate_id) REFERENCES gates (id) ON DELETE SET NULL
    """))


def downgrade():
    # Removes associations, but retains message rows and their other columns.
    op.execute(sa.text("""
        ALTER TABLE messagedb
        DROP FOREIGN KEY fk_messagedb_gate_id_gates,
        DROP INDEX ix_messagedb_gate_id,
        DROP COLUMN gate_id
    """))
