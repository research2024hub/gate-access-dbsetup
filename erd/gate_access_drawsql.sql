-- DrawSQL import (MySQL). Generated from app/db/models on 2026-09-30.
-- Simplified for diagramming: CHECK constraints, JSON defaults, expression indexes and table options removed.

CREATE TABLE account_types (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_account_types PRIMARY KEY (id), 
	CONSTRAINT uq_account_types_name UNIQUE (name)
);

CREATE TABLE estates (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(255) NOT NULL, 
	location_coordinates VARCHAR(255) NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_estates PRIMARY KEY (id), 
	CONSTRAINT uq_estates_name UNIQUE (name), 
	CONSTRAINT uq_estates_location_coordinates UNIQUE (location_coordinates)
);

CREATE TABLE messagedb (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	topic VARCHAR(100) NOT NULL, 
	message TEXT NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_messagedb PRIMARY KEY (id)
);

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
);

CREATE TABLE privileges (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_privileges PRIMARY KEY (id), 
	CONSTRAINT uq_privileges_name UNIQUE (name)
);

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
	CONSTRAINT pk_users PRIMARY KEY (id)
);

CREATE TABLE access_groups (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	estate_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_access_groups PRIMARY KEY (id), 
	CONSTRAINT uq_access_groups_name_estate UNIQUE (name, estate_id), 
	CONSTRAINT fk_access_groups_estate_id_estates FOREIGN KEY(estate_id) REFERENCES estates (id) ON DELETE CASCADE
);

CREATE TABLE account_type_privilege_links (
	account_type_id INTEGER NOT NULL, 
	privilege_id INTEGER NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_account_type_privilege_links PRIMARY KEY (account_type_id, privilege_id), 
	CONSTRAINT fk_account_type_privilege_links_account_type_id_account_types FOREIGN KEY(account_type_id) REFERENCES account_types (id) ON DELETE CASCADE, 
	CONSTRAINT fk_account_type_privilege_links_privilege_id_privileges FOREIGN KEY(privilege_id) REFERENCES privileges (id) ON DELETE CASCADE
);

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
);

CREATE TABLE user_reports (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	subject VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_user_reports PRIMARY KEY (id), 
	CONSTRAINT fk_user_reports_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE accesslog (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	license_plate_number VARCHAR(20) NOT NULL, 
	event VARCHAR(50) NOT NULL, 
	gate_id INTEGER NOT NULL, 
	timestamp DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_accesslog PRIMARY KEY (id), 
	CONSTRAINT fk_accesslog_gate_id_gates FOREIGN KEY(gate_id) REFERENCES gates (id) ON DELETE CASCADE
);

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
);

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
);

CREATE TABLE report_status (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	report_id INTEGER NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_report_status PRIMARY KEY (id), 
	CONSTRAINT uq_report_status_report_id UNIQUE (report_id), 
	CONSTRAINT fk_report_status_report_id_user_reports FOREIGN KEY(report_id) REFERENCES user_reports (id) ON DELETE CASCADE
);

CREATE TABLE system_metrics (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	gate_id INTEGER NOT NULL, 
	device_timestamp DATETIME(6) NOT NULL, 
	temperature_celsius NUMERIC(6, 3) NOT NULL, 
	total_cameras INTEGER NOT NULL, 
	online_cameras INTEGER NOT NULL, 
	running_services JSON NOT NULL, 
	storage_used_gb NUMERIC(12, 3) NOT NULL, 
	storage_total_gb NUMERIC(12, 3) NOT NULL, 
	offline_camera_ids JSON NOT NULL, 
	camera_alert_ts DATETIME(6), 
	received_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_system_metrics PRIMARY KEY (id), 
	CONSTRAINT fk_system_metrics_gate_id_gates FOREIGN KEY(gate_id) REFERENCES gates (id) ON DELETE CASCADE
);

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
);

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
);

CREATE TABLE personal_info_privilege_links (
	personal_info_id INTEGER NOT NULL, 
	privilege_id INTEGER NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_personal_info_privilege_links PRIMARY KEY (personal_info_id, privilege_id), 
	CONSTRAINT fk_personal_info_privilege_links_personal_info_id_personal_info FOREIGN KEY(personal_info_id) REFERENCES personal_info (id) ON DELETE CASCADE, 
	CONSTRAINT fk_personal_info_privilege_links_privilege_id_privileges FOREIGN KEY(privilege_id) REFERENCES privileges (id) ON DELETE CASCADE
);

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
);

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
	CONSTRAINT fk_events_creator_id_account_holders FOREIGN KEY(creator_id) REFERENCES account_holders (id) ON DELETE CASCADE
);

CREATE TABLE guests (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	personal_info_id INTEGER, 
	creator_id INTEGER, 
	status VARCHAR(20) NOT NULL DEFAULT 'EXPECTED', 
	other_info JSON NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_guests PRIMARY KEY (id), 
	CONSTRAINT fk_guests_personal_info_id_personal_info FOREIGN KEY(personal_info_id) REFERENCES personal_info (id) ON DELETE CASCADE, 
	CONSTRAINT fk_guests_creator_id_account_holders FOREIGN KEY(creator_id) REFERENCES account_holders (id) ON DELETE CASCADE
);

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
);

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
);

CREATE TABLE event_registers (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	event_id INTEGER NOT NULL, 
	guest_id INTEGER NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_event_registers PRIMARY KEY (id), 
	CONSTRAINT uq_event_registers_event_guest UNIQUE (event_id, guest_id), 
	CONSTRAINT fk_event_registers_event_id_events FOREIGN KEY(event_id) REFERENCES events (id) ON DELETE CASCADE, 
	CONSTRAINT fk_event_registers_guest_id_guests FOREIGN KEY(guest_id) REFERENCES guests (id) ON DELETE CASCADE
);

CREATE TABLE faces (
	id VARCHAR(64) NOT NULL, 
	guest_id INTEGER NOT NULL, 
	date_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	date_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	CONSTRAINT pk_faces PRIMARY KEY (id), 
	CONSTRAINT fk_faces_guest_id_guests FOREIGN KEY(guest_id) REFERENCES guests (id) ON DELETE CASCADE
);
