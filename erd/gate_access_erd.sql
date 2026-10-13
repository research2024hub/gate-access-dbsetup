-- MySQL schema export at mysql_0003. Use Alembic for installation.
CREATE TABLE account_types (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_account_types PRIMARY KEY (id), 
	CONSTRAINT uq_account_types_name UNIQUE (name)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE TABLE estates (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(255) NOT NULL, 
	location_coordinates VARCHAR(255) NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_estates PRIMARY KEY (id), 
	CONSTRAINT uq_estates_name UNIQUE (name), 
	CONSTRAINT uq_estates_location_coordinates UNIQUE (location_coordinates)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE TABLE pending_users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	email VARCHAR(255), 
	password VARCHAR(255) NOT NULL, 
	phone_number VARCHAR(20), 
	otp VARCHAR(255) NOT NULL, 
	otp_expiry DATETIME(6) NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_pending_users PRIMARY KEY (id), 
	CONSTRAINT uq_pending_users_email UNIQUE (email), 
	CONSTRAINT uq_pending_users_phone_number UNIQUE (phone_number)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE TABLE privileges (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_privileges PRIMARY KEY (id), 
	CONSTRAINT uq_privileges_name UNIQUE (name)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	email VARCHAR(255), 
	phone_number VARCHAR(20), 
	password VARCHAR(255) NOT NULL, 
	reset_otp VARCHAR(255), 
	reset_expiry DATETIME(6), 
	is_active BOOL NOT NULL DEFAULT true, 
	is_admin BOOL NOT NULL DEFAULT false, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	deleted_at DATETIME(6), 
	CONSTRAINT pk_users PRIMARY KEY (id), 
	CONSTRAINT ck_users_has_identifier CHECK (email IS NOT NULL OR phone_number IS NOT NULL)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_users_deleted_at ON users (deleted_at);

CREATE UNIQUE INDEX uq_users_email ON users ((CASE WHEN deleted_at IS NULL THEN email ELSE NULL END));

CREATE UNIQUE INDEX uq_users_phone_number ON users ((CASE WHEN deleted_at IS NULL THEN phone_number ELSE NULL END));

CREATE TABLE access_groups (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	estate_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_access_groups PRIMARY KEY (id), 
	CONSTRAINT uq_access_groups_name_estate UNIQUE (name, estate_id), 
	CONSTRAINT fk_access_groups_estate_id_estates FOREIGN KEY(estate_id) REFERENCES estates (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_access_groups_estate_id ON access_groups (estate_id);

CREATE TABLE account_type_privilege_links (
	account_type_id INTEGER NOT NULL, 
	privilege_id INTEGER NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_account_type_privilege_links PRIMARY KEY (account_type_id, privilege_id), 
	CONSTRAINT fk_account_type_privilege_links_account_type_id_account_types FOREIGN KEY(account_type_id) REFERENCES account_types (id) ON DELETE CASCADE, 
	CONSTRAINT fk_account_type_privilege_links_privilege_id_privileges FOREIGN KEY(privilege_id) REFERENCES privileges (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_account_type_privilege_links_privilege_id ON account_type_privilege_links (privilege_id);

CREATE TABLE gates (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	estate_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	last_controller_heartbeat DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	opening_time TIME NOT NULL DEFAULT '00:00:00', 
	closing_time TIME NOT NULL DEFAULT '23:59:59', 
	active BOOL NOT NULL DEFAULT true, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	last_alert_sent_at DATETIME(6), 
	snr VARCHAR(50), 
	rssi VARCHAR(50), 
	CONSTRAINT pk_gates PRIMARY KEY (id), 
	CONSTRAINT uq_gates_name_estate UNIQUE (name, estate_id), 
	CONSTRAINT fk_gates_estate_id_estates FOREIGN KEY(estate_id) REFERENCES estates (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_gates_estate_id ON gates (estate_id);

CREATE TABLE user_reports (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	subject VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_user_reports PRIMARY KEY (id), 
	CONSTRAINT fk_user_reports_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_user_reports_user_id ON user_reports (user_id);

CREATE TABLE accesslog (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	license_plate_number VARCHAR(20) NOT NULL, 
	event VARCHAR(50) NOT NULL, 
	gate_id INTEGER NOT NULL, 
	timestamp DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_accesslog PRIMARY KEY (id), 
	CONSTRAINT fk_accesslog_gate_id_gates FOREIGN KEY(gate_id) REFERENCES gates (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_accesslog_gate_id ON accesslog (gate_id);

CREATE INDEX ix_accesslog_license_plate_number_timestamp ON accesslog (license_plate_number, timestamp);

CREATE INDEX ix_accesslog_timestamp ON accesslog (timestamp);

CREATE TABLE gate_access_group_links (
	gate_id INTEGER NOT NULL, 
	access_group_id INTEGER NOT NULL, 
	opening_time TIME NOT NULL DEFAULT '00:00:00', 
	closing_time TIME NOT NULL DEFAULT '23:59:59', 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_gate_access_group_links PRIMARY KEY (gate_id, access_group_id), 
	CONSTRAINT fk_gate_access_group_links_gate_id_gates FOREIGN KEY(gate_id) REFERENCES gates (id) ON DELETE CASCADE, 
	CONSTRAINT fk_gate_access_group_links_access_group_id_access_groups FOREIGN KEY(access_group_id) REFERENCES access_groups (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_gate_access_group_links_access_group_id ON gate_access_group_links (access_group_id);

CREATE TABLE messagedb (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	gate_id INTEGER, 
	topic VARCHAR(100) NOT NULL, 
	message TEXT NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_messagedb PRIMARY KEY (id), 
	CONSTRAINT fk_messagedb_gate_id_gates FOREIGN KEY(gate_id) REFERENCES gates (id) ON DELETE SET NULL
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_messagedb_date_created ON messagedb (date_created);

CREATE INDEX ix_messagedb_gate_id ON messagedb (gate_id);

CREATE INDEX ix_messagedb_topic ON messagedb (topic);

CREATE TABLE personal_info (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	estate_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	id_type VARCHAR(50), 
	id_num VARCHAR(100), 
	contact VARCHAR(50), 
	expiry DATETIME(6), 
	account_type_id INTEGER NOT NULL DEFAULT 1, 
	access_group_id INTEGER NOT NULL DEFAULT 1, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_personal_info PRIMARY KEY (id), 
	CONSTRAINT uq_id_type_id_num UNIQUE (id_type, id_num, estate_id), 
	CONSTRAINT fk_personal_info_estate_id_estates FOREIGN KEY(estate_id) REFERENCES estates (id) ON DELETE CASCADE, 
	CONSTRAINT fk_personal_info_account_type_id_account_types FOREIGN KEY(account_type_id) REFERENCES account_types (id), 
	CONSTRAINT fk_personal_info_access_group_id_access_groups FOREIGN KEY(access_group_id) REFERENCES access_groups (id)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_personal_info_access_group_id ON personal_info (access_group_id);

CREATE INDEX ix_personal_info_account_type_id ON personal_info (account_type_id);

CREATE INDEX ix_personal_info_estate_id ON personal_info (estate_id);

CREATE TABLE report_status (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	report_id INTEGER NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_report_status PRIMARY KEY (id), 
	CONSTRAINT uq_report_status_report_id UNIQUE (report_id), 
	CONSTRAINT fk_report_status_report_id_user_reports FOREIGN KEY(report_id) REFERENCES user_reports (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE TABLE system_metrics (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	gate_id INTEGER NOT NULL, 
	device_timestamp DATETIME(6) NOT NULL, 
	temperature_celsius NUMERIC(6, 3) NOT NULL, 
	total_cameras INTEGER NOT NULL, 
	online_cameras INTEGER NOT NULL, 
	running_services JSON NOT NULL DEFAULT (JSON_OBJECT()), 
	storage_used_gb NUMERIC(12, 3) NOT NULL, 
	storage_total_gb NUMERIC(12, 3) NOT NULL, 
	offline_camera_ids JSON NOT NULL DEFAULT (JSON_ARRAY()), 
	camera_alert_ts DATETIME(6), 
	received_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_system_metrics PRIMARY KEY (id), 
	CONSTRAINT fk_system_metrics_gate_id_gates FOREIGN KEY(gate_id) REFERENCES gates (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_system_metrics_device_timestamp ON system_metrics (device_timestamp);

CREATE INDEX ix_system_metrics_gate_id ON system_metrics (gate_id);

CREATE INDEX ix_system_metrics_received_at ON system_metrics (received_at);

CREATE TABLE account_holders (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	personal_info_id INTEGER, 
	house_address VARCHAR(255) NOT NULL, 
	otp VARCHAR(255), 
	otp_generated_at DATETIME(6), 
	owner_account_holder_id INTEGER, 
	is_active BOOL NOT NULL DEFAULT false, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	deleted_at DATETIME(6), 
	CONSTRAINT pk_account_holders PRIMARY KEY (id), 
	CONSTRAINT fk_account_holders_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	CONSTRAINT fk_account_holders_personal_info_id_personal_info FOREIGN KEY(personal_info_id) REFERENCES personal_info (id) ON DELETE CASCADE, 
	CONSTRAINT fk_account_holders_owner_account_holder_id_account_holders FOREIGN KEY(owner_account_holder_id) REFERENCES account_holders (id) ON DELETE SET NULL
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_account_holders_deleted_at ON account_holders (deleted_at);

CREATE INDEX ix_account_holders_owner_account_holder_id ON account_holders (owner_account_holder_id);

CREATE INDEX ix_account_holders_personal_info_id ON account_holders (personal_info_id);

CREATE INDEX ix_account_holders_user_id ON account_holders (user_id);

CREATE TABLE personal_info_gate_links (
	gate_id INTEGER NOT NULL, 
	personal_info_id INTEGER NOT NULL, 
	opening_time TIME NOT NULL DEFAULT '00:00:00', 
	closing_time TIME NOT NULL DEFAULT '23:59:59', 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_personal_info_gate_links PRIMARY KEY (gate_id, personal_info_id), 
	CONSTRAINT fk_personal_info_gate_links_gate_id_gates FOREIGN KEY(gate_id) REFERENCES gates (id) ON DELETE CASCADE, 
	CONSTRAINT fk_personal_info_gate_links_personal_info_id_personal_info FOREIGN KEY(personal_info_id) REFERENCES personal_info (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_personal_info_gate_links_personal_info_id ON personal_info_gate_links (personal_info_id);

CREATE TABLE personal_info_privilege_links (
	personal_info_id INTEGER NOT NULL, 
	privilege_id INTEGER NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_personal_info_privilege_links PRIMARY KEY (personal_info_id, privilege_id), 
	CONSTRAINT fk_personal_info_privilege_links_personal_info_id_personal_info FOREIGN KEY(personal_info_id) REFERENCES personal_info (id) ON DELETE CASCADE, 
	CONSTRAINT fk_personal_info_privilege_links_privilege_id_privileges FOREIGN KEY(privilege_id) REFERENCES privileges (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_personal_info_privilege_links_privilege_id ON personal_info_privilege_links (privilege_id);

CREATE TABLE vehicles (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	personal_info_id INTEGER, 
	license_plate_number VARCHAR(20) NOT NULL, 
	make VARCHAR(100) NOT NULL, 
	model VARCHAR(100) NOT NULL, 
	color VARCHAR(50) NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_vehicles PRIMARY KEY (id), 
	CONSTRAINT fk_vehicles_personal_info_id_personal_info FOREIGN KEY(personal_info_id) REFERENCES personal_info (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_vehicles_license_plate_number ON vehicles (license_plate_number);

CREATE INDEX ix_vehicles_personal_info_id ON vehicles (personal_info_id);

CREATE TABLE events (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	creator_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	max_num_of_attendees INTEGER NOT NULL, 
	start_time DATETIME(6) NOT NULL, 
	end_time DATETIME(6) NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_events PRIMARY KEY (id), 
	CONSTRAINT ck_events_end_after_start CHECK (end_time > start_time), 
	CONSTRAINT fk_events_creator_id_account_holders FOREIGN KEY(creator_id) REFERENCES account_holders (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_events_creator_id ON events (creator_id);

CREATE TABLE guests (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	personal_info_id INTEGER, 
	creator_id INTEGER, 
	status VARCHAR(20) NOT NULL DEFAULT 'EXPECTED', 
	other_info JSON NOT NULL DEFAULT (JSON_OBJECT()), 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_guests PRIMARY KEY (id), 
	CONSTRAINT fk_guests_personal_info_id_personal_info FOREIGN KEY(personal_info_id) REFERENCES personal_info (id) ON DELETE CASCADE, 
	CONSTRAINT fk_guests_creator_id_account_holders FOREIGN KEY(creator_id) REFERENCES account_holders (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_guests_creator_id ON guests (creator_id);

CREATE INDEX ix_guests_personal_info_id ON guests (personal_info_id);

CREATE TABLE logs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	estate_id INTEGER, 
	target_account_holder_id INTEGER, 
	actor_user_id INTEGER, 
	type VARCHAR(50) NOT NULL, 
	message TEXT NOT NULL, 
	license_plate_number VARCHAR(20), 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_logs PRIMARY KEY (id), 
	CONSTRAINT fk_logs_estate_id_estates FOREIGN KEY(estate_id) REFERENCES estates (id) ON DELETE SET NULL, 
	CONSTRAINT fk_logs_target_account_holder_id_account_holders FOREIGN KEY(target_account_holder_id) REFERENCES account_holders (id) ON DELETE SET NULL, 
	CONSTRAINT fk_logs_actor_user_id_users FOREIGN KEY(actor_user_id) REFERENCES users (id) ON DELETE SET NULL
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_logs_actor_user_id ON logs (actor_user_id);

CREATE INDEX ix_logs_date_created ON logs (date_created);

CREATE INDEX ix_logs_estate_id ON logs (estate_id);

CREATE INDEX ix_logs_estate_id_date_created ON logs (estate_id, date_created);

CREATE INDEX ix_logs_license_plate_number ON logs (license_plate_number);

CREATE INDEX ix_logs_target_account_holder_id ON logs (target_account_holder_id);

CREATE INDEX ix_logs_type ON logs (type);

CREATE TABLE pending_account_holders (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	personal_info_id INTEGER, 
	house_address VARCHAR(255) NOT NULL, 
	otp VARCHAR(255), 
	otp_generated_at DATETIME(6), 
	owner_account_holder_id INTEGER, 
	is_pending BOOL NOT NULL DEFAULT true, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	email VARCHAR(255), 
	CONSTRAINT pk_pending_account_holders PRIMARY KEY (id), 
	CONSTRAINT fk_pending_account_holders_personal_info_id_personal_info FOREIGN KEY(personal_info_id) REFERENCES personal_info (id) ON DELETE CASCADE, 
	CONSTRAINT fk_pending_account_holders_owner_account_holder_id_accou_e6ac FOREIGN KEY(owner_account_holder_id) REFERENCES account_holders (id) ON DELETE CASCADE, 
	CONSTRAINT uq_pending_account_holders_email UNIQUE (email)
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_pending_account_holders_owner_account_holder_id ON pending_account_holders (owner_account_holder_id);

CREATE INDEX ix_pending_account_holders_personal_info_id ON pending_account_holders (personal_info_id);

CREATE TABLE event_registers (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	event_id INTEGER NOT NULL, 
	guest_id INTEGER NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_event_registers PRIMARY KEY (id), 
	CONSTRAINT uq_event_registers_event_guest UNIQUE (event_id, guest_id), 
	CONSTRAINT fk_event_registers_event_id_events FOREIGN KEY(event_id) REFERENCES events (id) ON DELETE CASCADE, 
	CONSTRAINT fk_event_registers_guest_id_guests FOREIGN KEY(guest_id) REFERENCES guests (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_event_registers_event_id ON event_registers (event_id);

CREATE INDEX ix_event_registers_guest_id ON event_registers (guest_id);

CREATE TABLE faces (
	id VARCHAR(64) NOT NULL, 
	guest_id INTEGER NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_faces PRIMARY KEY (id), 
	CONSTRAINT fk_faces_guest_id_guests FOREIGN KEY(guest_id) REFERENCES guests (id) ON DELETE CASCADE
)CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin;

CREATE INDEX ix_faces_guest_id ON faces (guest_id);

DELIMITER $$

CREATE TRIGGER `account_types_date_updated` BEFORE UPDATE ON `account_types`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `estates_date_updated` BEFORE UPDATE ON `estates`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `pending_users_date_updated` BEFORE UPDATE ON `pending_users`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `privileges_date_updated` BEFORE UPDATE ON `privileges`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `users_date_updated` BEFORE UPDATE ON `users`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `access_groups_date_updated` BEFORE UPDATE ON `access_groups`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `account_type_privilege_links_date_updated` BEFORE UPDATE ON `account_type_privilege_links`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `gates_date_updated` BEFORE UPDATE ON `gates`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `user_reports_date_updated` BEFORE UPDATE ON `user_reports`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `gate_access_group_links_date_updated` BEFORE UPDATE ON `gate_access_group_links`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `personal_info_date_updated` BEFORE UPDATE ON `personal_info`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `report_status_date_updated` BEFORE UPDATE ON `report_status`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `account_holders_date_updated` BEFORE UPDATE ON `account_holders`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `personal_info_gate_links_date_updated` BEFORE UPDATE ON `personal_info_gate_links`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `personal_info_privilege_links_date_updated` BEFORE UPDATE ON `personal_info_privilege_links`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `vehicles_date_updated` BEFORE UPDATE ON `vehicles`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `events_date_updated` BEFORE UPDATE ON `events`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `guests_date_updated` BEFORE UPDATE ON `guests`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `pending_account_holders_date_updated` BEFORE UPDATE ON `pending_account_holders`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER `faces_date_updated` BEFORE UPDATE ON `faces`
FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)
$$

CREATE TRIGGER estate_access_group AFTER INSERT ON estates FOR EACH ROW
INSERT INTO access_groups (estate_id, name) VALUES (NEW.id, 'REGULAR')
$$

CREATE TRIGGER account_holder_estate_insert BEFORE INSERT ON account_holders FOR EACH ROW
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
          AND ah.deleted_at IS NULL AND TRUE;
        IF existing_memberships > 0 THEN
            SIGNAL SQLSTATE '23000' SET MYSQL_ERRNO = 1062,
                MESSAGE_TEXT = 'User already has an active membership in this estate';
        END IF;
    END IF;
END
$$

CREATE TRIGGER account_holder_estate_update BEFORE UPDATE ON account_holders FOR EACH ROW
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
          AND ah.deleted_at IS NULL AND ah.id <> OLD.id;
        IF existing_memberships > 0 THEN
            SIGNAL SQLSTATE '23000' SET MYSQL_ERRNO = 1062,
                MESSAGE_TEXT = 'User already has an active membership in this estate';
        END IF;
    END IF;
END
$$

CREATE TRIGGER personal_info_estate_guard BEFORE UPDATE ON personal_info FOR EACH ROW
BEGIN
    IF NEW.estate_id <> OLD.estate_id AND EXISTS (
        SELECT 1 FROM account_holders WHERE personal_info_id = OLD.id FOR SHARE
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT =
            'Move membership to a new personal_info record instead of changing its estate';
    END IF;
END
$$

CREATE TRIGGER event_capacity_insert BEFORE INSERT ON event_registers FOR EACH ROW
BEGIN
    DECLARE capacity INTEGER;
    DECLARE used_places INTEGER;
    IF TRUE THEN
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
$$

CREATE TRIGGER event_capacity_update BEFORE UPDATE ON event_registers FOR EACH ROW
BEGIN
    DECLARE capacity INTEGER;
    DECLARE used_places INTEGER;
    IF NEW.event_id <> OLD.event_id THEN
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
$$
DELIMITER ;
