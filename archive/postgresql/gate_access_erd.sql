-- ============================================================================
-- Gate Access DB Setup — ERD schema
-- Derived from app/db/models/*.py (SQLAlchemy models)
--
-- HOW TO IMPORT INTO LUCIDCHART:
--   1. In Lucidchart: File > Import Data > "SQL" (or the "Import from SQL" / ERD wizard).
--   2. Upload this file. Lucid will parse the CREATE TABLE + FOREIGN KEY
--      statements and auto-generate an entity-relationship diagram with
--      crow's-foot connectors.
--   3. Tables are ordered so every FOREIGN KEY target is already defined.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Foundation
-- ---------------------------------------------------------------------------
CREATE TABLE estates (
    id                     SERIAL PRIMARY KEY,
    name                   VARCHAR NOT NULL UNIQUE,
    location_coordinates   VARCHAR NOT NULL UNIQUE,
    date_created           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id             SERIAL PRIMARY KEY,
    email          VARCHAR,
    phone_number   VARCHAR,
    password       VARCHAR NOT NULL,
    reset_otp      VARCHAR,
    reset_expiry   TIMESTAMP,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin       BOOLEAN NOT NULL DEFAULT FALSE,
    date_created   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pending_users (
    id             SERIAL PRIMARY KEY,
    email          VARCHAR UNIQUE,
    password       VARCHAR NOT NULL,
    phone_number   VARCHAR,
    otp            VARCHAR NOT NULL,
    otp_expiry     TIMESTAMP NOT NULL,
    date_created   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE account_types (
    id             SERIAL PRIMARY KEY,
    name           VARCHAR NOT NULL UNIQUE,
    date_created   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE privileges (
    id             SERIAL PRIMARY KEY,
    name           VARCHAR NOT NULL UNIQUE,
    date_created   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Estate-scoped access infrastructure
-- ---------------------------------------------------------------------------
CREATE TABLE access_groups (
    id             SERIAL PRIMARY KEY,
    estate_id      INTEGER NOT NULL REFERENCES estates(id) ON DELETE CASCADE,
    name           VARCHAR NOT NULL,
    date_created   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_access_groups_name_estate UNIQUE (name, estate_id)
);

CREATE TABLE gates (
    id                          SERIAL PRIMARY KEY,
    estate_id                   INTEGER NOT NULL REFERENCES estates(id) ON DELETE CASCADE,
    name                        VARCHAR NOT NULL,
    last_controller_heartbeat   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    opening_time                TIME NOT NULL DEFAULT '00:00:00',
    closing_time                TIME NOT NULL DEFAULT '23:59:59',
    active                      BOOLEAN NOT NULL DEFAULT TRUE,
    date_created                TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated                TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_alert_sent_at          TIMESTAMP,
    snr                         VARCHAR,
    rssi                        VARCHAR,
    CONSTRAINT uq_gates_name_estate UNIQUE (name, estate_id)
);

-- ---------------------------------------------------------------------------
-- Central identity record (residents, staff, vendors, guests all key off this)
-- ---------------------------------------------------------------------------
CREATE TABLE personal_info (
    id                SERIAL PRIMARY KEY,
    estate_id         INTEGER NOT NULL REFERENCES estates(id) ON DELETE CASCADE,
    name              VARCHAR NOT NULL,
    id_type           VARCHAR,
    id_num            VARCHAR,
    contact           VARCHAR,
    expiry            TIMESTAMP,
    account_type_id   INTEGER NOT NULL DEFAULT 1 REFERENCES account_types(id),
    access_group_id   INTEGER NOT NULL DEFAULT 1 REFERENCES access_groups(id),
    date_created      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_id_type_id_num UNIQUE (id_type, id_num, estate_id)
);

-- ---------------------------------------------------------------------------
-- Many-to-many link/junction tables
-- ---------------------------------------------------------------------------
CREATE TABLE account_type_privilege_links (
    account_type_id   INTEGER NOT NULL REFERENCES account_types(id) ON DELETE CASCADE,
    privilege_id      INTEGER NOT NULL REFERENCES privileges(id) ON DELETE CASCADE,
    date_created      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (account_type_id, privilege_id)
);

CREATE TABLE personal_info_privilege_links (
    personal_info_id   INTEGER NOT NULL REFERENCES personal_info(id) ON DELETE CASCADE,
    privilege_id        INTEGER NOT NULL REFERENCES privileges(id) ON DELETE CASCADE,
    date_created         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (personal_info_id, privilege_id)
);

CREATE TABLE gate_access_group_links (
    gate_id           INTEGER NOT NULL REFERENCES gates(id) ON DELETE CASCADE,
    access_group_id   INTEGER NOT NULL REFERENCES access_groups(id) ON DELETE CASCADE,
    opening_time      TIME NOT NULL DEFAULT '00:00:00',
    closing_time      TIME NOT NULL DEFAULT '23:59:59',
    date_created      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (gate_id, access_group_id)
);

CREATE TABLE personal_info_gate_links (
    gate_id             INTEGER NOT NULL REFERENCES gates(id) ON DELETE CASCADE,
    personal_info_id    INTEGER NOT NULL REFERENCES personal_info(id) ON DELETE CASCADE,
    opening_time        TIME NOT NULL DEFAULT '00:00:00',
    closing_time        TIME NOT NULL DEFAULT '23:59:59',
    date_created         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (gate_id, personal_info_id)
);

-- ---------------------------------------------------------------------------
-- Account holders (residents) — self-referencing for sub-accounts
-- ---------------------------------------------------------------------------
CREATE TABLE account_holders (
    id                        SERIAL PRIMARY KEY,
    user_id                   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    personal_info_id          INTEGER REFERENCES personal_info(id) ON DELETE CASCADE,
    house_address             VARCHAR NOT NULL,
    otp                       VARCHAR,
    otp_generated_at          TIMESTAMP,
    owner_account_holder_id   INTEGER REFERENCES account_holders(id) ON DELETE CASCADE,
    is_active                 BOOLEAN NOT NULL DEFAULT FALSE,
    date_created              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pending_account_holders (
    id                        SERIAL PRIMARY KEY,
    personal_info_id          INTEGER REFERENCES personal_info(id) ON DELETE CASCADE,
    house_address             VARCHAR NOT NULL,
    otp                       VARCHAR,
    otp_generated_at          TIMESTAMP,
    owner_account_holder_id   INTEGER REFERENCES account_holders(id) ON DELETE CASCADE,
    is_pending                BOOLEAN NOT NULL DEFAULT TRUE,
    date_created              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    email                     VARCHAR
);

-- ---------------------------------------------------------------------------
-- Guests, faces, vehicles
-- ---------------------------------------------------------------------------
CREATE TABLE guests (
    id                  SERIAL PRIMARY KEY,
    personal_info_id    INTEGER REFERENCES personal_info(id) ON DELETE CASCADE,
    creator_id          INTEGER REFERENCES users(id) ON DELETE CASCADE,
    status              VARCHAR NOT NULL DEFAULT 'EXPECTED',
    other_info          JSONB NOT NULL DEFAULT '{}'::jsonb,
    date_created        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE faces (
    id             VARCHAR PRIMARY KEY,
    guest_id       INTEGER NOT NULL REFERENCES guests(id) ON DELETE CASCADE,
    date_created   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vehicles (
    id                      SERIAL PRIMARY KEY,
    personal_info_id        INTEGER REFERENCES personal_info(id) ON DELETE CASCADE,
    license_plate_number    VARCHAR NOT NULL,
    make                    VARCHAR NOT NULL,
    model                   VARCHAR NOT NULL,
    color                   VARCHAR NOT NULL,
    date_created            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Events
-- ---------------------------------------------------------------------------
CREATE TABLE events (
    id                      SERIAL PRIMARY KEY,
    creator_id              INTEGER NOT NULL REFERENCES account_holders(id) ON DELETE CASCADE,
    name                    VARCHAR NOT NULL,
    max_num_of_attendees    INTEGER NOT NULL,
    start_time              TIMESTAMP NOT NULL,
    end_time                TIMESTAMP NOT NULL,
    date_created            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE event_registers (
    id             SERIAL PRIMARY KEY,
    event_id       INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    guest_id       INTEGER NOT NULL REFERENCES guests(id) ON DELETE CASCADE,
    date_created   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- Logging, telemetry, messaging
-- ---------------------------------------------------------------------------
CREATE TABLE accesslog (
    id                       SERIAL PRIMARY KEY,
    license_plate_number     VARCHAR NOT NULL,
    event                    VARCHAR NOT NULL,
    gate_id                  INTEGER NOT NULL REFERENCES gates(id) ON DELETE CASCADE,
    timestamp                TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE system_metrics (
    id                     SERIAL PRIMARY KEY,
    gate_id                INTEGER NOT NULL REFERENCES gates(id) ON DELETE CASCADE,
    device_timestamp       TIMESTAMP NOT NULL,
    temperature_celsius    NUMERIC NOT NULL,
    total_cameras          INTEGER NOT NULL,
    online_cameras         INTEGER NOT NULL,
    running_services       JSONB NOT NULL DEFAULT '{}'::jsonb,
    storage_used_gb        NUMERIC NOT NULL,
    storage_total_gb       NUMERIC NOT NULL,
    offline_camera_ids     JSONB NOT NULL DEFAULT '{}'::jsonb,
    camera_alert_ts        TIMESTAMP,
    received_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE logs (
    id                          SERIAL PRIMARY KEY,
    estate_id                   INTEGER REFERENCES estates(id) ON DELETE CASCADE,
    target_account_holder_id    INTEGER REFERENCES account_holders(id) ON DELETE CASCADE,
    actor_user_id               INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type                        VARCHAR NOT NULL,
    message                     VARCHAR NOT NULL,
    date_created                TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messagedb (
    id             SERIAL PRIMARY KEY,
    topic          VARCHAR NOT NULL,
    message        VARCHAR NOT NULL,
    date_created   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- User reports
-- ---------------------------------------------------------------------------
CREATE TABLE user_reports (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject        VARCHAR NOT NULL,
    description    VARCHAR NOT NULL,
    date_created   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE report_status (
    id             SERIAL PRIMARY KEY,
    report_id      INTEGER NOT NULL REFERENCES user_reports(id) ON DELETE CASCADE,
    status         VARCHAR NOT NULL,
    date_created   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_updated   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
