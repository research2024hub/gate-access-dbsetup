"""add missing fk indexes

Revision ID: a1b2c3d4e5f6
Revises: 951ce3ad0c0d
Create Date: 2026-08-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '951ce3ad0c0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (index_name, table_name, column_name) for every FK column that wasn't
# already covered by an existing index (PK or unique constraint).
INDEXES = [
    ("ix_access_groups_estate_id", "access_groups", "estate_id"),
    ("ix_accesslog_gate_id", "accesslog", "gate_id"),
    ("ix_account_holders_user_id", "account_holders", "user_id"),
    ("ix_account_holders_personal_info_id", "account_holders", "personal_info_id"),
    ("ix_account_holders_owner_account_holder_id", "account_holders", "owner_account_holder_id"),
    ("ix_account_type_privilege_links_privilege_id", "account_type_privilege_links", "privilege_id"),
    ("ix_event_registers_event_id", "event_registers", "event_id"),
    ("ix_event_registers_guest_id", "event_registers", "guest_id"),
    ("ix_events_creator_id", "events", "creator_id"),
    ("ix_faces_guest_id", "faces", "guest_id"),
    ("ix_gate_access_group_links_access_group_id", "gate_access_group_links", "access_group_id"),
    ("ix_gates_estate_id", "gates", "estate_id"),
    ("ix_guests_personal_info_id", "guests", "personal_info_id"),
    ("ix_guests_creator_id", "guests", "creator_id"),
    ("ix_logs_estate_id", "logs", "estate_id"),
    ("ix_logs_target_account_holder_id", "logs", "target_account_holder_id"),
    ("ix_logs_actor_user_id", "logs", "actor_user_id"),
    ("ix_system_metrics_gate_id", "system_metrics", "gate_id"),
    ("ix_pending_account_holders_personal_info_id", "pending_account_holders", "personal_info_id"),
    ("ix_pending_account_holders_owner_account_holder_id", "pending_account_holders", "owner_account_holder_id"),
    ("ix_personal_info_gate_links_personal_info_id", "personal_info_gate_links", "personal_info_id"),
    ("ix_personal_info_privilege_links_privilege_id", "personal_info_privilege_links", "privilege_id"),
    ("ix_personal_info_estate_id", "personal_info", "estate_id"),
    ("ix_personal_info_account_type_id", "personal_info", "account_type_id"),
    ("ix_personal_info_access_group_id", "personal_info", "access_group_id"),
    ("ix_report_status_report_id", "report_status", "report_id"),
    ("ix_user_reports_user_id", "user_reports", "user_id"),
    ("ix_vehicles_personal_info_id", "vehicles", "personal_info_id"),
]


def upgrade() -> None:
    for index_name, table_name, column_name in INDEXES:
        op.create_index(index_name, table_name, [column_name])


def downgrade() -> None:
    for index_name, table_name, column_name in reversed(INDEXES):
        op.drop_index(index_name, table_name=table_name)
