"""MySQL trigger definitions. Changes require a new Alembic revision."""

def trigger_statements(tables):
    for table in tables:
        if 'date_updated' in table.c:
            yield (f'{table.name}_date_updated', f'''
CREATE TRIGGER `{table.name}_date_updated` BEFORE UPDATE ON `{table.name}`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
''')
    yield ('estate_access_group', '''
CREATE TRIGGER estate_access_group AFTER INSERT ON estates FOR EACH ROW
INSERT INTO access_groups (estate_id, name) VALUES (NEW.id, 'REGULAR')
''')
    for operation in ('INSERT', 'UPDATE'):
        name = 'account_holder_estate_' + operation.lower()
        # Lock a stable parent row to serialize membership writes for this user.
        # Nonlocking counts require READ COMMITTED after the parent lock.
        exclude_self = 'TRUE' if operation == 'INSERT' else 'ah.id <> OLD.id'
        yield (name, f'''
CREATE TRIGGER {name} BEFORE {operation} ON account_holders FOR EACH ROW
BEGIN
    DECLARE estate_value INTEGER DEFAULT NULL;
    DECLARE locked_user INTEGER;
    DECLARE existing_memberships INTEGER DEFAULT 0;
    IF NEW.deleted_at IS NULL AND NEW.personal_info_id IS NOT NULL THEN
        IF @@session.transaction_isolation <> 'READ-COMMITTED' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Gate Access writes require READ COMMITTED isolation';
        END IF;
        SELECT estate_id INTO estate_value FROM personal_info
        WHERE id = NEW.personal_info_id FOR SHARE;
        SELECT id INTO locked_user FROM users WHERE id = NEW.user_id FOR UPDATE;
        SELECT COUNT(*) INTO existing_memberships
        FROM account_holders ah JOIN personal_info pi ON pi.id = ah.personal_info_id
        WHERE ah.user_id = NEW.user_id AND pi.estate_id = estate_value
          AND ah.deleted_at IS NULL AND {exclude_self};
        IF existing_memberships > 0 THEN
            SIGNAL SQLSTATE '23000' SET MYSQL_ERRNO = 1062,
                MESSAGE_TEXT = 'User already has an active membership in this estate';
        END IF;
    END IF;
END
''')
    yield ('personal_info_estate_guard', '''
CREATE TRIGGER personal_info_estate_guard BEFORE UPDATE ON personal_info FOR EACH ROW
BEGIN
    IF NEW.estate_id <> OLD.estate_id AND EXISTS (
        SELECT 1 FROM account_holders WHERE personal_info_id = OLD.id FOR SHARE
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT =
            'Move membership to a new personal_info record instead of changing its estate';
    END IF;
END
''')
    for operation in ('INSERT', 'UPDATE'):
        name = 'event_capacity_' + operation.lower()
        condition = 'TRUE' if operation == 'INSERT' else 'NEW.event_id <> OLD.event_id'
        yield (name, f'''
CREATE TRIGGER {name} BEFORE {operation} ON event_registers FOR EACH ROW
BEGIN
    DECLARE capacity INTEGER;
    DECLARE used_places INTEGER;
    IF {condition} THEN
        IF @@session.transaction_isolation <> 'READ-COMMITTED' THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Gate Access writes require READ COMMITTED isolation';
        END IF;
        SELECT max_num_of_attendees INTO capacity FROM events
        WHERE id = NEW.event_id FOR UPDATE;
        SELECT COUNT(*) INTO used_places FROM event_registers
        WHERE event_id = NEW.event_id;
        IF used_places >= capacity THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Event has reached its maximum number of attendees';
        END IF;
    END IF;
END
''')
