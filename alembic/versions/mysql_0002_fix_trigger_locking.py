"""Repair self-table locking reads; writes require READ COMMITTED.

Pause application writes during upgrade/downgrade: MySQL trigger DDL auto-commits.
"""
from alembic import op
import sqlalchemy as sa

revision = 'mysql_0002'
down_revision = 'mysql_0001'
branch_labels = None
depends_on = None

OLD_TRIGGERS = [('account_holder_estate_insert',
  '\n'
  'CREATE TRIGGER account_holder_estate_insert BEFORE INSERT ON '
  'account_holders FOR EACH ROW\n'
  'BEGIN\n'
  '    DECLARE estate_value INTEGER DEFAULT NULL;\n'
  '    DECLARE locked_user INTEGER;\n'
  '    DECLARE existing_memberships INTEGER DEFAULT 0;\n'
  '    IF NEW.deleted_at IS NULL AND NEW.personal_info_id IS NOT NULL THEN\n'
  '        SELECT estate_id INTO estate_value FROM personal_info\n'
  '        WHERE id = NEW.personal_info_id FOR SHARE;\n'
  '        SELECT id INTO locked_user FROM users WHERE id = NEW.user_id FOR '
  'UPDATE;\n'
  '        SELECT COUNT(*) INTO existing_memberships\n'
  '        FROM account_holders ah JOIN personal_info pi ON pi.id = '
  'ah.personal_info_id\n'
  '        WHERE ah.user_id = NEW.user_id AND pi.estate_id = estate_value\n'
  '          AND ah.deleted_at IS NULL AND TRUE\n'
  '        FOR UPDATE;\n'
  '        IF existing_memberships > 0 THEN\n'
  "            SIGNAL SQLSTATE '23000' SET MYSQL_ERRNO = 1062,\n"
  "                MESSAGE_TEXT = 'User already has an active membership in "
  "this estate';\n"
  '        END IF;\n'
  '    END IF;\n'
  'END\n'),
 ('account_holder_estate_update',
  '\n'
  'CREATE TRIGGER account_holder_estate_update BEFORE UPDATE ON '
  'account_holders FOR EACH ROW\n'
  'BEGIN\n'
  '    DECLARE estate_value INTEGER DEFAULT NULL;\n'
  '    DECLARE locked_user INTEGER;\n'
  '    DECLARE existing_memberships INTEGER DEFAULT 0;\n'
  '    IF NEW.deleted_at IS NULL AND NEW.personal_info_id IS NOT NULL THEN\n'
  '        SELECT estate_id INTO estate_value FROM personal_info\n'
  '        WHERE id = NEW.personal_info_id FOR SHARE;\n'
  '        SELECT id INTO locked_user FROM users WHERE id = NEW.user_id FOR '
  'UPDATE;\n'
  '        SELECT COUNT(*) INTO existing_memberships\n'
  '        FROM account_holders ah JOIN personal_info pi ON pi.id = '
  'ah.personal_info_id\n'
  '        WHERE ah.user_id = NEW.user_id AND pi.estate_id = estate_value\n'
  '          AND ah.deleted_at IS NULL AND ah.id <> OLD.id\n'
  '        FOR UPDATE;\n'
  '        IF existing_memberships > 0 THEN\n'
  "            SIGNAL SQLSTATE '23000' SET MYSQL_ERRNO = 1062,\n"
  "                MESSAGE_TEXT = 'User already has an active membership in "
  "this estate';\n"
  '        END IF;\n'
  '    END IF;\n'
  'END\n'),
 ('event_capacity_insert',
  '\n'
  'CREATE TRIGGER event_capacity_insert BEFORE INSERT ON event_registers FOR '
  'EACH ROW\n'
  'BEGIN\n'
  '    DECLARE capacity INTEGER;\n'
  '    DECLARE used_places INTEGER;\n'
  '    IF TRUE THEN\n'
  '        SELECT max_num_of_attendees INTO capacity FROM events\n'
  '        WHERE id = NEW.event_id FOR UPDATE;\n'
  '        SELECT COUNT(*) INTO used_places FROM event_registers\n'
  '        WHERE event_id = NEW.event_id FOR UPDATE;\n'
  '        IF used_places >= capacity THEN\n'
  "            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Event has reached "
  "its maximum number of attendees';\n"
  '        END IF;\n'
  '    END IF;\n'
  'END\n'),
 ('event_capacity_update',
  '\n'
  'CREATE TRIGGER event_capacity_update BEFORE UPDATE ON event_registers FOR '
  'EACH ROW\n'
  'BEGIN\n'
  '    DECLARE capacity INTEGER;\n'
  '    DECLARE used_places INTEGER;\n'
  '    IF NEW.event_id <> OLD.event_id THEN\n'
  '        SELECT max_num_of_attendees INTO capacity FROM events\n'
  '        WHERE id = NEW.event_id FOR UPDATE;\n'
  '        SELECT COUNT(*) INTO used_places FROM event_registers\n'
  '        WHERE event_id = NEW.event_id FOR UPDATE;\n'
  '        IF used_places >= capacity THEN\n'
  "            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Event has reached "
  "its maximum number of attendees';\n"
  '        END IF;\n'
  '    END IF;\n'
  'END\n')]

NEW_TRIGGERS = [('account_holder_estate_insert',
  '\n'
  'CREATE TRIGGER account_holder_estate_insert BEFORE INSERT ON '
  'account_holders FOR EACH ROW\n'
  'BEGIN\n'
  '    DECLARE estate_value INTEGER DEFAULT NULL;\n'
  '    DECLARE locked_user INTEGER;\n'
  '    DECLARE existing_memberships INTEGER DEFAULT 0;\n'
  '    IF NEW.deleted_at IS NULL AND NEW.personal_info_id IS NOT NULL THEN\n'
  "        IF @@session.transaction_isolation <> 'READ-COMMITTED' THEN\n"
  "            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Gate Access writes "
  "require READ COMMITTED isolation';\n"
  '        END IF;\n'
  '        SELECT estate_id INTO estate_value FROM personal_info\n'
  '        WHERE id = NEW.personal_info_id FOR SHARE;\n'
  '        SELECT id INTO locked_user FROM users WHERE id = NEW.user_id FOR '
  'UPDATE;\n'
  '        SELECT COUNT(*) INTO existing_memberships\n'
  '        FROM account_holders ah JOIN personal_info pi ON pi.id = '
  'ah.personal_info_id\n'
  '        WHERE ah.user_id = NEW.user_id AND pi.estate_id = estate_value\n'
  '          AND ah.deleted_at IS NULL AND TRUE;\n'
  '        IF existing_memberships > 0 THEN\n'
  "            SIGNAL SQLSTATE '23000' SET MYSQL_ERRNO = 1062,\n"
  "                MESSAGE_TEXT = 'User already has an active membership in "
  "this estate';\n"
  '        END IF;\n'
  '    END IF;\n'
  'END\n'),
 ('account_holder_estate_update',
  '\n'
  'CREATE TRIGGER account_holder_estate_update BEFORE UPDATE ON '
  'account_holders FOR EACH ROW\n'
  'BEGIN\n'
  '    DECLARE estate_value INTEGER DEFAULT NULL;\n'
  '    DECLARE locked_user INTEGER;\n'
  '    DECLARE existing_memberships INTEGER DEFAULT 0;\n'
  '    IF NEW.deleted_at IS NULL AND NEW.personal_info_id IS NOT NULL THEN\n'
  "        IF @@session.transaction_isolation <> 'READ-COMMITTED' THEN\n"
  "            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Gate Access writes "
  "require READ COMMITTED isolation';\n"
  '        END IF;\n'
  '        SELECT estate_id INTO estate_value FROM personal_info\n'
  '        WHERE id = NEW.personal_info_id FOR SHARE;\n'
  '        SELECT id INTO locked_user FROM users WHERE id = NEW.user_id FOR '
  'UPDATE;\n'
  '        SELECT COUNT(*) INTO existing_memberships\n'
  '        FROM account_holders ah JOIN personal_info pi ON pi.id = '
  'ah.personal_info_id\n'
  '        WHERE ah.user_id = NEW.user_id AND pi.estate_id = estate_value\n'
  '          AND ah.deleted_at IS NULL AND ah.id <> OLD.id;\n'
  '        IF existing_memberships > 0 THEN\n'
  "            SIGNAL SQLSTATE '23000' SET MYSQL_ERRNO = 1062,\n"
  "                MESSAGE_TEXT = 'User already has an active membership in "
  "this estate';\n"
  '        END IF;\n'
  '    END IF;\n'
  'END\n'),
 ('event_capacity_insert',
  '\n'
  'CREATE TRIGGER event_capacity_insert BEFORE INSERT ON event_registers FOR '
  'EACH ROW\n'
  'BEGIN\n'
  '    DECLARE capacity INTEGER;\n'
  '    DECLARE used_places INTEGER;\n'
  '    IF TRUE THEN\n'
  "        IF @@session.transaction_isolation <> 'READ-COMMITTED' THEN\n"
  "            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Gate Access writes "
  "require READ COMMITTED isolation';\n"
  '        END IF;\n'
  '        SELECT max_num_of_attendees INTO capacity FROM events\n'
  '        WHERE id = NEW.event_id FOR UPDATE;\n'
  '        SELECT COUNT(*) INTO used_places FROM event_registers\n'
  '        WHERE event_id = NEW.event_id;\n'
  '        IF used_places >= capacity THEN\n'
  "            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Event has reached "
  "its maximum number of attendees';\n"
  '        END IF;\n'
  '    END IF;\n'
  'END\n'),
 ('event_capacity_update',
  '\n'
  'CREATE TRIGGER event_capacity_update BEFORE UPDATE ON event_registers FOR '
  'EACH ROW\n'
  'BEGIN\n'
  '    DECLARE capacity INTEGER;\n'
  '    DECLARE used_places INTEGER;\n'
  '    IF NEW.event_id <> OLD.event_id THEN\n'
  "        IF @@session.transaction_isolation <> 'READ-COMMITTED' THEN\n"
  "            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Gate Access writes "
  "require READ COMMITTED isolation';\n"
  '        END IF;\n'
  '        SELECT max_num_of_attendees INTO capacity FROM events\n'
  '        WHERE id = NEW.event_id FOR UPDATE;\n'
  '        SELECT COUNT(*) INTO used_places FROM event_registers\n'
  '        WHERE event_id = NEW.event_id;\n'
  '        IF used_places >= capacity THEN\n'
  "            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Event has reached "
  "its maximum number of attendees';\n"
  '        END IF;\n'
  '    END IF;\n'
  'END\n')]

def replace_triggers(definitions):
    for name, ddl in definitions:
        op.execute(sa.text('DROP TRIGGER IF EXISTS `' + name + '`'))
        op.execute(sa.text(ddl))


def upgrade():
    replace_triggers(NEW_TRIGGERS)


def downgrade():
    replace_triggers(OLD_TRIGGERS)
