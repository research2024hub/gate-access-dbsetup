"""MySQL 8.4 baseline (fresh database only)."""
from alembic import op
import sqlalchemy as sa
revision = 'mysql_0001'
down_revision = None
branch_labels = None
depends_on = None

DDL = ['CREATE TABLE account_types (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\tname VARCHAR(100) NOT NULL, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_account_types PRIMARY KEY (id), \n'
 '\tCONSTRAINT uq_account_types_name UNIQUE (name)\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE TABLE estates (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\tname VARCHAR(255) NOT NULL, \n'
 '\tlocation_coordinates VARCHAR(255) NOT NULL, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_estates PRIMARY KEY (id), \n'
 '\tCONSTRAINT uq_estates_name UNIQUE (name), \n'
 '\tCONSTRAINT uq_estates_location_coordinates UNIQUE (location_coordinates)\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE TABLE messagedb (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\ttopic VARCHAR(100) NOT NULL, \n'
 '\tmessage TEXT NOT NULL, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_messagedb PRIMARY KEY (id)\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_messagedb_date_created ON messagedb (date_created)',
 'CREATE INDEX ix_messagedb_topic ON messagedb (topic)',
 'CREATE TABLE pending_users (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\temail VARCHAR(255), \n'
 '\tpassword VARCHAR(255) NOT NULL, \n'
 '\tphone_number VARCHAR(20), \n'
 '\totp VARCHAR(255) NOT NULL, \n'
 '\totp_expiry DATETIME(6) NOT NULL, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_pending_users PRIMARY KEY (id), \n'
 '\tCONSTRAINT uq_pending_users_email UNIQUE (email), \n'
 '\tCONSTRAINT uq_pending_users_phone_number UNIQUE (phone_number)\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE TABLE privileges (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\tname VARCHAR(100) NOT NULL, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_privileges PRIMARY KEY (id), \n'
 '\tCONSTRAINT uq_privileges_name UNIQUE (name)\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE TABLE users (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\temail VARCHAR(255), \n'
 '\tphone_number VARCHAR(20), \n'
 '\tpassword VARCHAR(255) NOT NULL, \n'
 '\treset_otp VARCHAR(255), \n'
 '\treset_expiry DATETIME(6), \n'
 '\tis_active BOOL NOT NULL DEFAULT true, \n'
 '\tis_admin BOOL NOT NULL DEFAULT false, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdeleted_at DATETIME(6), \n'
 '\tCONSTRAINT pk_users PRIMARY KEY (id), \n'
 '\tCONSTRAINT ck_users_has_identifier CHECK (email IS NOT NULL OR phone_number IS NOT NULL)\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_users_deleted_at ON users (deleted_at)',
 'CREATE UNIQUE INDEX uq_users_email ON users ((CASE WHEN deleted_at IS NULL THEN email ELSE NULL '
 'END))',
 'CREATE UNIQUE INDEX uq_users_phone_number ON users ((CASE WHEN deleted_at IS NULL THEN '
 'phone_number ELSE NULL END))',
 'CREATE TABLE access_groups (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\testate_id INTEGER NOT NULL, \n'
 '\tname VARCHAR(255) NOT NULL, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_access_groups PRIMARY KEY (id), \n'
 '\tCONSTRAINT uq_access_groups_name_estate UNIQUE (name, estate_id), \n'
 '\tCONSTRAINT fk_access_groups_estate_id_estates FOREIGN KEY(estate_id) REFERENCES estates (id) '
 'ON DELETE CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_access_groups_estate_id ON access_groups (estate_id)',
 'CREATE TABLE account_type_privilege_links (\n'
 '\taccount_type_id INTEGER NOT NULL, \n'
 '\tprivilege_id INTEGER NOT NULL, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_account_type_privilege_links PRIMARY KEY (account_type_id, privilege_id), \n'
 '\tCONSTRAINT fk_account_type_privilege_links_account_type_id_account_types FOREIGN '
 'KEY(account_type_id) REFERENCES account_types (id) ON DELETE CASCADE, \n'
 '\tCONSTRAINT fk_account_type_privilege_links_privilege_id_privileges FOREIGN KEY(privilege_id) '
 'REFERENCES privileges (id) ON DELETE CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_account_type_privilege_links_privilege_id ON account_type_privilege_links '
 '(privilege_id)',
 'CREATE TABLE gates (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\testate_id INTEGER NOT NULL, \n'
 '\tname VARCHAR(255) NOT NULL, \n'
 '\tlast_controller_heartbeat DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 "\topening_time TIME NOT NULL DEFAULT '00:00:00', \n"
 "\tclosing_time TIME NOT NULL DEFAULT '23:59:59', \n"
 '\tactive BOOL NOT NULL DEFAULT true, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tlast_alert_sent_at DATETIME(6), \n'
 '\tsnr VARCHAR(50), \n'
 '\trssi VARCHAR(50), \n'
 '\tCONSTRAINT pk_gates PRIMARY KEY (id), \n'
 '\tCONSTRAINT uq_gates_name_estate UNIQUE (name, estate_id), \n'
 '\tCONSTRAINT fk_gates_estate_id_estates FOREIGN KEY(estate_id) REFERENCES estates (id) ON DELETE '
 'CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_gates_estate_id ON gates (estate_id)',
 'CREATE TABLE user_reports (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\tuser_id INTEGER NOT NULL, \n'
 '\tsubject VARCHAR(255) NOT NULL, \n'
 '\tdescription TEXT NOT NULL, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_user_reports PRIMARY KEY (id), \n'
 '\tCONSTRAINT fk_user_reports_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE '
 'CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_user_reports_user_id ON user_reports (user_id)',
 'CREATE TABLE accesslog (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\tlicense_plate_number VARCHAR(20) NOT NULL, \n'
 '\tevent VARCHAR(50) NOT NULL, \n'
 '\tgate_id INTEGER NOT NULL, \n'
 '\ttimestamp DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_accesslog PRIMARY KEY (id), \n'
 '\tCONSTRAINT fk_accesslog_gate_id_gates FOREIGN KEY(gate_id) REFERENCES gates (id) ON DELETE '
 'CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_accesslog_gate_id ON accesslog (gate_id)',
 'CREATE INDEX ix_accesslog_license_plate_number_timestamp ON accesslog (license_plate_number, '
 'timestamp)',
 'CREATE INDEX ix_accesslog_timestamp ON accesslog (timestamp)',
 'CREATE TABLE gate_access_group_links (\n'
 '\tgate_id INTEGER NOT NULL, \n'
 '\taccess_group_id INTEGER NOT NULL, \n'
 "\topening_time TIME NOT NULL DEFAULT '00:00:00', \n"
 "\tclosing_time TIME NOT NULL DEFAULT '23:59:59', \n"
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_gate_access_group_links PRIMARY KEY (gate_id, access_group_id), \n'
 '\tCONSTRAINT fk_gate_access_group_links_gate_id_gates FOREIGN KEY(gate_id) REFERENCES gates (id) '
 'ON DELETE CASCADE, \n'
 '\tCONSTRAINT fk_gate_access_group_links_access_group_id_access_groups FOREIGN '
 'KEY(access_group_id) REFERENCES access_groups (id) ON DELETE CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_gate_access_group_links_access_group_id ON gate_access_group_links '
 '(access_group_id)',
 'CREATE TABLE personal_info (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\testate_id INTEGER NOT NULL, \n'
 '\tname VARCHAR(255) NOT NULL, \n'
 '\tid_type VARCHAR(50), \n'
 '\tid_num VARCHAR(100), \n'
 '\tcontact VARCHAR(50), \n'
 '\texpiry DATETIME(6), \n'
 '\taccount_type_id INTEGER NOT NULL DEFAULT 1, \n'
 '\taccess_group_id INTEGER NOT NULL DEFAULT 1, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_personal_info PRIMARY KEY (id), \n'
 '\tCONSTRAINT uq_id_type_id_num UNIQUE (id_type, id_num, estate_id), \n'
 '\tCONSTRAINT fk_personal_info_estate_id_estates FOREIGN KEY(estate_id) REFERENCES estates (id) '
 'ON DELETE CASCADE, \n'
 '\tCONSTRAINT fk_personal_info_account_type_id_account_types FOREIGN KEY(account_type_id) '
 'REFERENCES account_types (id), \n'
 '\tCONSTRAINT fk_personal_info_access_group_id_access_groups FOREIGN KEY(access_group_id) '
 'REFERENCES access_groups (id)\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_personal_info_access_group_id ON personal_info (access_group_id)',
 'CREATE INDEX ix_personal_info_account_type_id ON personal_info (account_type_id)',
 'CREATE INDEX ix_personal_info_estate_id ON personal_info (estate_id)',
 'CREATE TABLE report_status (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\treport_id INTEGER NOT NULL, \n'
 '\tstatus VARCHAR(50) NOT NULL, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_report_status PRIMARY KEY (id), \n'
 '\tCONSTRAINT uq_report_status_report_id UNIQUE (report_id), \n'
 '\tCONSTRAINT fk_report_status_report_id_user_reports FOREIGN KEY(report_id) REFERENCES '
 'user_reports (id) ON DELETE CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE TABLE system_metrics (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\tgate_id INTEGER NOT NULL, \n'
 '\tdevice_timestamp DATETIME(6) NOT NULL, \n'
 '\ttemperature_celsius NUMERIC(6, 3) NOT NULL, \n'
 '\ttotal_cameras INTEGER NOT NULL, \n'
 '\tonline_cameras INTEGER NOT NULL, \n'
 '\trunning_services JSON NOT NULL DEFAULT (JSON_OBJECT()), \n'
 '\tstorage_used_gb NUMERIC(12, 3) NOT NULL, \n'
 '\tstorage_total_gb NUMERIC(12, 3) NOT NULL, \n'
 '\toffline_camera_ids JSON NOT NULL DEFAULT (JSON_ARRAY()), \n'
 '\tcamera_alert_ts DATETIME(6), \n'
 '\treceived_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_system_metrics PRIMARY KEY (id), \n'
 '\tCONSTRAINT fk_system_metrics_gate_id_gates FOREIGN KEY(gate_id) REFERENCES gates (id) ON '
 'DELETE CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_system_metrics_device_timestamp ON system_metrics (device_timestamp)',
 'CREATE INDEX ix_system_metrics_gate_id ON system_metrics (gate_id)',
 'CREATE INDEX ix_system_metrics_received_at ON system_metrics (received_at)',
 'CREATE TABLE account_holders (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\tuser_id INTEGER NOT NULL, \n'
 '\tpersonal_info_id INTEGER, \n'
 '\thouse_address VARCHAR(255) NOT NULL, \n'
 '\totp VARCHAR(255), \n'
 '\totp_generated_at DATETIME(6), \n'
 '\towner_account_holder_id INTEGER, \n'
 '\tis_active BOOL NOT NULL DEFAULT false, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdeleted_at DATETIME(6), \n'
 '\tCONSTRAINT pk_account_holders PRIMARY KEY (id), \n'
 '\tCONSTRAINT fk_account_holders_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON '
 'DELETE CASCADE, \n'
 '\tCONSTRAINT fk_account_holders_personal_info_id_personal_info FOREIGN KEY(personal_info_id) '
 'REFERENCES personal_info (id) ON DELETE CASCADE, \n'
 '\tCONSTRAINT fk_account_holders_owner_account_holder_id_account_holders FOREIGN '
 'KEY(owner_account_holder_id) REFERENCES account_holders (id) ON DELETE SET NULL\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_account_holders_deleted_at ON account_holders (deleted_at)',
 'CREATE INDEX ix_account_holders_owner_account_holder_id ON account_holders '
 '(owner_account_holder_id)',
 'CREATE INDEX ix_account_holders_personal_info_id ON account_holders (personal_info_id)',
 'CREATE INDEX ix_account_holders_user_id ON account_holders (user_id)',
 'CREATE TABLE personal_info_gate_links (\n'
 '\tgate_id INTEGER NOT NULL, \n'
 '\tpersonal_info_id INTEGER NOT NULL, \n'
 "\topening_time TIME NOT NULL DEFAULT '00:00:00', \n"
 "\tclosing_time TIME NOT NULL DEFAULT '23:59:59', \n"
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_personal_info_gate_links PRIMARY KEY (gate_id, personal_info_id), \n'
 '\tCONSTRAINT fk_personal_info_gate_links_gate_id_gates FOREIGN KEY(gate_id) REFERENCES gates '
 '(id) ON DELETE CASCADE, \n'
 '\tCONSTRAINT fk_personal_info_gate_links_personal_info_id_personal_info FOREIGN '
 'KEY(personal_info_id) REFERENCES personal_info (id) ON DELETE CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_personal_info_gate_links_personal_info_id ON personal_info_gate_links '
 '(personal_info_id)',
 'CREATE TABLE personal_info_privilege_links (\n'
 '\tpersonal_info_id INTEGER NOT NULL, \n'
 '\tprivilege_id INTEGER NOT NULL, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_personal_info_privilege_links PRIMARY KEY (personal_info_id, privilege_id), \n'
 '\tCONSTRAINT fk_personal_info_privilege_links_personal_info_id_personal_info FOREIGN '
 'KEY(personal_info_id) REFERENCES personal_info (id) ON DELETE CASCADE, \n'
 '\tCONSTRAINT fk_personal_info_privilege_links_privilege_id_privileges FOREIGN KEY(privilege_id) '
 'REFERENCES privileges (id) ON DELETE CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_personal_info_privilege_links_privilege_id ON personal_info_privilege_links '
 '(privilege_id)',
 'CREATE TABLE vehicles (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\tpersonal_info_id INTEGER, \n'
 '\tlicense_plate_number VARCHAR(20) NOT NULL, \n'
 '\tmake VARCHAR(100) NOT NULL, \n'
 '\tmodel VARCHAR(100) NOT NULL, \n'
 '\tcolor VARCHAR(50) NOT NULL, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_vehicles PRIMARY KEY (id), \n'
 '\tCONSTRAINT fk_vehicles_personal_info_id_personal_info FOREIGN KEY(personal_info_id) REFERENCES '
 'personal_info (id) ON DELETE CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_vehicles_license_plate_number ON vehicles (license_plate_number)',
 'CREATE INDEX ix_vehicles_personal_info_id ON vehicles (personal_info_id)',
 'CREATE TABLE events (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\tcreator_id INTEGER NOT NULL, \n'
 '\tname VARCHAR(255) NOT NULL, \n'
 '\tmax_num_of_attendees INTEGER NOT NULL, \n'
 '\tstart_time DATETIME(6) NOT NULL, \n'
 '\tend_time DATETIME(6) NOT NULL, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_events PRIMARY KEY (id), \n'
 '\tCONSTRAINT ck_events_end_after_start CHECK (end_time > start_time), \n'
 '\tCONSTRAINT fk_events_creator_id_account_holders FOREIGN KEY(creator_id) REFERENCES '
 'account_holders (id) ON DELETE CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_events_creator_id ON events (creator_id)',
 'CREATE TABLE guests (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\tpersonal_info_id INTEGER, \n'
 '\tcreator_id INTEGER, \n'
 "\tstatus VARCHAR(20) NOT NULL DEFAULT 'EXPECTED', \n"
 '\tother_info JSON NOT NULL DEFAULT (JSON_OBJECT()), \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_guests PRIMARY KEY (id), \n'
 '\tCONSTRAINT fk_guests_personal_info_id_personal_info FOREIGN KEY(personal_info_id) REFERENCES '
 'personal_info (id) ON DELETE CASCADE, \n'
 '\tCONSTRAINT fk_guests_creator_id_account_holders FOREIGN KEY(creator_id) REFERENCES '
 'account_holders (id) ON DELETE CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_guests_creator_id ON guests (creator_id)',
 'CREATE INDEX ix_guests_personal_info_id ON guests (personal_info_id)',
 'CREATE TABLE logs (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\testate_id INTEGER, \n'
 '\ttarget_account_holder_id INTEGER, \n'
 '\tactor_user_id INTEGER, \n'
 '\ttype VARCHAR(50) NOT NULL, \n'
 '\tmessage TEXT NOT NULL, \n'
 '\tlicense_plate_number VARCHAR(20), \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_logs PRIMARY KEY (id), \n'
 '\tCONSTRAINT fk_logs_estate_id_estates FOREIGN KEY(estate_id) REFERENCES estates (id) ON DELETE '
 'SET NULL, \n'
 '\tCONSTRAINT fk_logs_target_account_holder_id_account_holders FOREIGN '
 'KEY(target_account_holder_id) REFERENCES account_holders (id) ON DELETE SET NULL, \n'
 '\tCONSTRAINT fk_logs_actor_user_id_users FOREIGN KEY(actor_user_id) REFERENCES users (id) ON '
 'DELETE SET NULL\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_logs_actor_user_id ON logs (actor_user_id)',
 'CREATE INDEX ix_logs_date_created ON logs (date_created)',
 'CREATE INDEX ix_logs_estate_id ON logs (estate_id)',
 'CREATE INDEX ix_logs_estate_id_date_created ON logs (estate_id, date_created)',
 'CREATE INDEX ix_logs_license_plate_number ON logs (license_plate_number)',
 'CREATE INDEX ix_logs_target_account_holder_id ON logs (target_account_holder_id)',
 'CREATE INDEX ix_logs_type ON logs (type)',
 'CREATE TABLE pending_account_holders (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\tpersonal_info_id INTEGER, \n'
 '\thouse_address VARCHAR(255) NOT NULL, \n'
 '\totp VARCHAR(255), \n'
 '\totp_generated_at DATETIME(6), \n'
 '\towner_account_holder_id INTEGER, \n'
 '\tis_pending BOOL NOT NULL DEFAULT true, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\temail VARCHAR(255), \n'
 '\tCONSTRAINT pk_pending_account_holders PRIMARY KEY (id), \n'
 '\tCONSTRAINT fk_pending_account_holders_personal_info_id_personal_info FOREIGN '
 'KEY(personal_info_id) REFERENCES personal_info (id) ON DELETE CASCADE, \n'
 '\tCONSTRAINT fk_pending_account_holders_owner_account_holder_id_accou_e6ac FOREIGN '
 'KEY(owner_account_holder_id) REFERENCES account_holders (id) ON DELETE CASCADE, \n'
 '\tCONSTRAINT uq_pending_account_holders_email UNIQUE (email)\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_pending_account_holders_owner_account_holder_id ON pending_account_holders '
 '(owner_account_holder_id)',
 'CREATE INDEX ix_pending_account_holders_personal_info_id ON pending_account_holders '
 '(personal_info_id)',
 'CREATE TABLE event_registers (\n'
 '\tid INTEGER NOT NULL AUTO_INCREMENT, \n'
 '\tevent_id INTEGER NOT NULL, \n'
 '\tguest_id INTEGER NOT NULL, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_event_registers PRIMARY KEY (id), \n'
 '\tCONSTRAINT uq_event_registers_event_guest UNIQUE (event_id, guest_id), \n'
 '\tCONSTRAINT fk_event_registers_event_id_events FOREIGN KEY(event_id) REFERENCES events (id) ON '
 'DELETE CASCADE, \n'
 '\tCONSTRAINT fk_event_registers_guest_id_guests FOREIGN KEY(guest_id) REFERENCES guests (id) ON '
 'DELETE CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_event_registers_event_id ON event_registers (event_id)',
 'CREATE INDEX ix_event_registers_guest_id ON event_registers (guest_id)',
 'CREATE TABLE faces (\n'
 '\tid VARCHAR(64) NOT NULL, \n'
 '\tguest_id INTEGER NOT NULL, \n'
 '\tdate_created DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tdate_updated DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), \n'
 '\tCONSTRAINT pk_faces PRIMARY KEY (id), \n'
 '\tCONSTRAINT fk_faces_guest_id_guests FOREIGN KEY(guest_id) REFERENCES guests (id) ON DELETE '
 'CASCADE\n'
 ')CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_bin',
 'CREATE INDEX ix_faces_guest_id ON faces (guest_id)']
TRIGGERS = [('account_types_date_updated',
  '\n'
  'CREATE TRIGGER `account_types_date_updated` BEFORE UPDATE ON `account_types`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('estates_date_updated',
  '\n'
  'CREATE TRIGGER `estates_date_updated` BEFORE UPDATE ON `estates`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('pending_users_date_updated',
  '\n'
  'CREATE TRIGGER `pending_users_date_updated` BEFORE UPDATE ON `pending_users`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('privileges_date_updated',
  '\n'
  'CREATE TRIGGER `privileges_date_updated` BEFORE UPDATE ON `privileges`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('users_date_updated',
  '\n'
  'CREATE TRIGGER `users_date_updated` BEFORE UPDATE ON `users`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('access_groups_date_updated',
  '\n'
  'CREATE TRIGGER `access_groups_date_updated` BEFORE UPDATE ON `access_groups`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('account_type_privilege_links_date_updated',
  '\n'
  'CREATE TRIGGER `account_type_privilege_links_date_updated` BEFORE UPDATE ON '
  '`account_type_privilege_links`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('gates_date_updated',
  '\n'
  'CREATE TRIGGER `gates_date_updated` BEFORE UPDATE ON `gates`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('user_reports_date_updated',
  '\n'
  'CREATE TRIGGER `user_reports_date_updated` BEFORE UPDATE ON `user_reports`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('gate_access_group_links_date_updated',
  '\n'
  'CREATE TRIGGER `gate_access_group_links_date_updated` BEFORE UPDATE ON '
  '`gate_access_group_links`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('personal_info_date_updated',
  '\n'
  'CREATE TRIGGER `personal_info_date_updated` BEFORE UPDATE ON `personal_info`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('report_status_date_updated',
  '\n'
  'CREATE TRIGGER `report_status_date_updated` BEFORE UPDATE ON `report_status`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('account_holders_date_updated',
  '\n'
  'CREATE TRIGGER `account_holders_date_updated` BEFORE UPDATE ON `account_holders`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('personal_info_gate_links_date_updated',
  '\n'
  'CREATE TRIGGER `personal_info_gate_links_date_updated` BEFORE UPDATE ON '
  '`personal_info_gate_links`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('personal_info_privilege_links_date_updated',
  '\n'
  'CREATE TRIGGER `personal_info_privilege_links_date_updated` BEFORE UPDATE ON '
  '`personal_info_privilege_links`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('vehicles_date_updated',
  '\n'
  'CREATE TRIGGER `vehicles_date_updated` BEFORE UPDATE ON `vehicles`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('events_date_updated',
  '\n'
  'CREATE TRIGGER `events_date_updated` BEFORE UPDATE ON `events`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('guests_date_updated',
  '\n'
  'CREATE TRIGGER `guests_date_updated` BEFORE UPDATE ON `guests`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('pending_account_holders_date_updated',
  '\n'
  'CREATE TRIGGER `pending_account_holders_date_updated` BEFORE UPDATE ON '
  '`pending_account_holders`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('faces_date_updated',
  '\n'
  'CREATE TRIGGER `faces_date_updated` BEFORE UPDATE ON `faces`\n'
  'FOR EACH ROW SET NEW.date_updated = UTC_TIMESTAMP(6)\n'),
 ('estate_access_group',
  '\n'
  'CREATE TRIGGER estate_access_group AFTER INSERT ON estates FOR EACH ROW\n'
  "INSERT INTO access_groups (estate_id, name) VALUES (NEW.id, 'REGULAR')\n"),
 ('account_holder_estate_insert',
  '\n'
  'CREATE TRIGGER account_holder_estate_insert BEFORE INSERT ON account_holders FOR EACH ROW\n'
  'BEGIN\n'
  '    DECLARE estate_value INTEGER DEFAULT NULL;\n'
  '    DECLARE locked_user INTEGER;\n'
  '    DECLARE existing_memberships INTEGER DEFAULT 0;\n'
  '    IF NEW.deleted_at IS NULL AND NEW.personal_info_id IS NOT NULL THEN\n'
  '        SELECT estate_id INTO estate_value FROM personal_info\n'
  '        WHERE id = NEW.personal_info_id FOR SHARE;\n'
  '        SELECT id INTO locked_user FROM users WHERE id = NEW.user_id FOR UPDATE;\n'
  '        SELECT COUNT(*) INTO existing_memberships\n'
  '        FROM account_holders ah JOIN personal_info pi ON pi.id = ah.personal_info_id\n'
  '        WHERE ah.user_id = NEW.user_id AND pi.estate_id = estate_value\n'
  '          AND ah.deleted_at IS NULL AND TRUE\n'
  '        FOR UPDATE;\n'
  '        IF existing_memberships > 0 THEN\n'
  "            SIGNAL SQLSTATE '23000' SET MYSQL_ERRNO = 1062,\n"
  "                MESSAGE_TEXT = 'User already has an active membership in this estate';\n"
  '        END IF;\n'
  '    END IF;\n'
  'END\n'),
 ('account_holder_estate_update',
  '\n'
  'CREATE TRIGGER account_holder_estate_update BEFORE UPDATE ON account_holders FOR EACH ROW\n'
  'BEGIN\n'
  '    DECLARE estate_value INTEGER DEFAULT NULL;\n'
  '    DECLARE locked_user INTEGER;\n'
  '    DECLARE existing_memberships INTEGER DEFAULT 0;\n'
  '    IF NEW.deleted_at IS NULL AND NEW.personal_info_id IS NOT NULL THEN\n'
  '        SELECT estate_id INTO estate_value FROM personal_info\n'
  '        WHERE id = NEW.personal_info_id FOR SHARE;\n'
  '        SELECT id INTO locked_user FROM users WHERE id = NEW.user_id FOR UPDATE;\n'
  '        SELECT COUNT(*) INTO existing_memberships\n'
  '        FROM account_holders ah JOIN personal_info pi ON pi.id = ah.personal_info_id\n'
  '        WHERE ah.user_id = NEW.user_id AND pi.estate_id = estate_value\n'
  '          AND ah.deleted_at IS NULL AND ah.id <> OLD.id\n'
  '        FOR UPDATE;\n'
  '        IF existing_memberships > 0 THEN\n'
  "            SIGNAL SQLSTATE '23000' SET MYSQL_ERRNO = 1062,\n"
  "                MESSAGE_TEXT = 'User already has an active membership in this estate';\n"
  '        END IF;\n'
  '    END IF;\n'
  'END\n'),
 ('personal_info_estate_guard',
  '\n'
  'CREATE TRIGGER personal_info_estate_guard BEFORE UPDATE ON personal_info FOR EACH ROW\n'
  'BEGIN\n'
  '    IF NEW.estate_id <> OLD.estate_id AND EXISTS (\n'
  '        SELECT 1 FROM account_holders WHERE personal_info_id = OLD.id FOR SHARE\n'
  '    ) THEN\n'
  "        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT =\n"
  "            'Move membership to a new personal_info record instead of changing its estate';\n"
  '    END IF;\n'
  'END\n'),
 ('event_capacity_insert',
  '\n'
  'CREATE TRIGGER event_capacity_insert BEFORE INSERT ON event_registers FOR EACH ROW\n'
  'BEGIN\n'
  '    DECLARE capacity INTEGER;\n'
  '    DECLARE used_places INTEGER;\n'
  '    IF TRUE THEN\n'
  '        SELECT max_num_of_attendees INTO capacity FROM events\n'
  '        WHERE id = NEW.event_id FOR UPDATE;\n'
  '        SELECT COUNT(*) INTO used_places FROM event_registers\n'
  '        WHERE event_id = NEW.event_id FOR UPDATE;\n'
  '        IF used_places >= capacity THEN\n'
  "            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Event has reached its maximum number of "
  "attendees';\n"
  '        END IF;\n'
  '    END IF;\n'
  'END\n'),
 ('event_capacity_update',
  '\n'
  'CREATE TRIGGER event_capacity_update BEFORE UPDATE ON event_registers FOR EACH ROW\n'
  'BEGIN\n'
  '    DECLARE capacity INTEGER;\n'
  '    DECLARE used_places INTEGER;\n'
  '    IF NEW.event_id <> OLD.event_id THEN\n'
  '        SELECT max_num_of_attendees INTO capacity FROM events\n'
  '        WHERE id = NEW.event_id FOR UPDATE;\n'
  '        SELECT COUNT(*) INTO used_places FROM event_registers\n'
  '        WHERE event_id = NEW.event_id FOR UPDATE;\n'
  '        IF used_places >= capacity THEN\n'
  "            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Event has reached its maximum number of "
  "attendees';\n"
  '        END IF;\n'
  '    END IF;\n'
  'END\n')]
TABLES = ['account_types',
 'estates',
 'messagedb',
 'pending_users',
 'privileges',
 'users',
 'access_groups',
 'account_type_privilege_links',
 'gates',
 'user_reports',
 'accesslog',
 'gate_access_group_links',
 'personal_info',
 'report_status',
 'system_metrics',
 'account_holders',
 'personal_info_gate_links',
 'personal_info_privilege_links',
 'vehicles',
 'events',
 'guests',
 'logs',
 'pending_account_holders',
 'event_registers',
 'faces']


def upgrade():
    if not op.get_context().as_sql:
        existing = set(sa.inspect(op.get_bind()).get_table_names()) - {'alembic_version'}
        if existing:
            raise RuntimeError('MySQL baseline requires an empty database; existing tables were found.')
    for statement in DDL:
        op.execute(sa.text(statement))
    for _, statement in TRIGGERS:
        op.execute(sa.text(statement))


def downgrade():
    for name, _ in reversed(TRIGGERS):
        op.execute(sa.text('DROP TRIGGER IF EXISTS `' + name + '`'))
    for name in reversed(TABLES):
        op.drop_table(name)
