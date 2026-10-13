# Database Production-Readiness Review

**Scope:** All 40 Alembic migrations in `alembic/versions/`.
**Reviewed:** 2026-08-21
**Migration chain:** Linear, single head (`d4e5f6a7b8c9`). No branches or multiple heads — good.

This document reconstructs the **final schema** (after applying every migration) and grades each
table. It is a schema/design review, not a data-correctness audit of live rows.

---

## TL;DR — verdict per table

| Table | Verdict | Headline reason |
|---|---|---|
| `account_types` | ✅ OK | Seeded lookup table, unique name, timestamps + touch trigger |
| `privileges` | ✅ OK | Seeded lookup table, unique name |
| `access_groups` | ✅ OK | Composite unique, FK indexed, cascade correct |
| `account_type_privilege_links` | ✅ OK | Clean junction table |
| `gate_access_group_links` | ✅ OK | Clean junction table |
| `personal_info_gate_links` | ✅ OK* | Fine, but no `date_updated` touch trigger (see cross-cutting) |
| `personal_info_privilege_links` | ✅ OK* | Same trigger gap |
| `faces` | ✅ OK | String PK (hash), FK indexed, trigger present |
| `estates` | 🟢 Mostly OK | `location_coordinates` as a *unique string* is a design smell |
| `gates` | 🟢 Mostly OK | `snr`/`rssi` as free strings; naive time columns |
| `vehicles` | 🟢 Mostly OK | `license_plate_number` not unique / not indexed by plate |
| `guests` | 🟡 Needs work | `status` is a free-text string, no CHECK/enum |
| `logs` | 🟡 Needs work | No index on `date_created`/`type` for an audit table |
| `events` | 🟡 Needs work | No `end_time > start_time` check; capacity trigger has a race |
| `event_registers` | 🟡 Needs work | **No unique `(event_id, guest_id)`** → duplicate registrations |
| `personal_info` | 🟡 Needs work | Identity columns made nullable — weakens the unique key |
| `system_metrics` | 🟡 Needs work | High-growth table, no time index, no retention/partitioning |
| `user_reports` | 🟡 Needs work | `date_updated` never auto-updates (no trigger) |
| `report_status` | 🟡 Needs work | Free-text `status`; no touch trigger |
| `messagedb` | 🟡 Needs work | No index on `topic`, no retention |
| `account_holders` | 🔴 Security/logic | Plaintext OTP; self-referential CASCADE; unique-per-estate trigger race |
| `users` | 🔴 Security | Plaintext `reset_otp`; both identifiers nullable (no "at least one" guard) |
| `pending_users` | 🔴 Security | Plaintext password **and** OTP; no retention/expiry cleanup |
| `pending_account_holders` | 🔴 Security | Plaintext OTP; no retention cleanup |

Legend: ✅ good · 🟢 minor polish · 🟡 real gaps to close before scale · 🔴 fix before production (security/data-integrity).

---

## What you got right (genuinely solid foundations)

These are the things that make the schema look deliberately built rather than auto-generated:

- **Every table has a primary key**, and every foreign key has an explicit `ondelete` policy chosen per-relationship (CASCADE for ownership, SET NULL for the audit trail).
- **`date_created` / `date_updated`** are standard across tables, backed by a `set_date_updated()` trigger for the original 14 tables.
- **Composite unique constraints** where they matter (`name+estate_id` on gates/access_groups, `id_type+id_num+estate_id` on personal_info).
- **You went back and added the missing FK indexes** (`a1b2c3d4e5f6`) — and correctly *skipped* FK columns already covered by a PK/unique leading column. That's the kind of detail most people miss.
- **You softened the `logs` FKs from CASCADE to SET NULL** (`b2c3d4e5f6a7`) so deleting a user/estate doesn't erase the audit trail. Correct instinct for an audit table.
- **Business rules enforced in the DB** via triggers (max attendees, one-account-per-user-per-estate, auto-create REGULAR access group per estate). Good that they live in the DB and not only in app code — with the caveat about races below.
- **Late unique constraints on login identifiers** (`users.email/phone`, pending tables) close real duplicate-account holes.

---

## Tables that are fine to work with as-is

`account_types`, `privileges`, `access_groups`, `account_type_privilege_links`,
`gate_access_group_links`, `personal_info_gate_links`, `personal_info_privilege_links`, `faces`.

Lookup/junction tables with correct keys, cascades, and indexes. The only nit is that the two
`personal_info_*_links` tables carry a `date_updated` column that never auto-updates (see below) —
harmless for pure junction tables.

`estates`, `gates`, `vehicles` are effectively fine — only cosmetic issues noted in the table above.

---

## Tables that need work (with the specific fix)

### 🔴 `users`
- **`reset_otp` stored in plaintext** (`String(20)`). Password-reset tokens should be stored hashed, or moved to a short-lived store. Anyone with read access to the row can reset the account.
- **Both `email` and `phone_number` are nullable** with no guard that *at least one* is present. A row can exist with no login identifier at all. Add a `CHECK (email IS NOT NULL OR phone_number IS NOT NULL)`.
- Unique constraints on email/phone were only added in Aug 2026 — **verify no historical duplicates exist** before trusting them (the constraint creation would have failed if so, but confirm it actually ran).

### 🔴 `account_holders`
- **Plaintext `otp`** (re-added in `50dd30564d9b` after being removed in `395669e858f6`). Same hashing concern as above. The add/drop/re-add churn also suggests the app's OTP model isn't settled.
- **`owner_account_holder_id` is a self-FK with `ondelete='CASCADE'`** — deleting a parent account holder silently deletes the whole sub-account chain beneath it. Confirm that's intended; SET NULL is usually safer.
- **`enforce_unique_user_per_estate` trigger is a check-then-insert (TOCTOU) race** — two concurrent inserts can both pass the `COUNT(*)` check and both commit, producing exactly the duplicate it's meant to prevent. A trigger can't be fully safe here; consider a functional/partial unique index or serializable-isolation handling.

### 🔴 `pending_users` / `pending_account_holders`
- **`pending_users` stores both the password and the OTP in plaintext.** Even for a staging/signup table this is sensitive — hash the password on write, hash/short-TTL the OTP.
- **No retention/cleanup.** These are ephemeral by design but nothing purges stale rows. Add a scheduled delete (e.g. `WHERE otp_expiry < now()` / `date_created < now() - interval '1 day'`).

### 🟡 `event_registers`
- **No unique `(event_id, guest_id)` constraint** — the same guest can be registered to the same event multiple times, and each one counts against the capacity trigger. Add the unique constraint.
- The **`enforce_max_attendees` trigger has the same count-then-insert race** as above; under concurrent registration you can exceed `max_num_of_attendees`.

### 🟡 `events`
- **No `CHECK (end_time > start_time)`.** Nothing stops an event that ends before it starts.
- `start_time`/`end_time` are naive `DateTime` (see timezone section).

### 🟡 `personal_info`
- Migration `cb1fbaca859a` made **`id_type`, `id_num`, `contact` nullable.** Because the identity key is `UNIQUE(id_type, id_num, estate_id)` and Postgres treats NULLs as distinct, rows with NULL id fields **bypass the uniqueness guarantee** entirely. If these are meant to identify a person, either keep them NOT NULL or add a partial unique index / `NULLS NOT DISTINCT`.
- FKs to `account_type_id` / `access_group_id` have **no `ondelete`** (default RESTRICT). That's a safe default, just be aware deletes of a referenced type/group will be blocked.

### 🟡 `guests`, `logs`, `report_status`
- **Status/type columns are free-text strings** (`guests.status`, `logs.type`, `report_status.status`). No CHECK constraint or enum, so typos and unexpected values slip in. Add CHECK constraints or Postgres enums for the known value sets.
- **`logs` has no index on `date_created` or `type`.** An audit table is almost always queried by time and/or type — add at least `ix_logs_date_created` (or a composite `(estate_id, date_created)`).

### 🟡 `system_metrics`
- This is the **fastest-growing table** (per-gate telemetry) and the least prepared for scale:
  - **No index on `device_timestamp` / `received_at`** — time-range queries will table-scan.
  - **No retention or partitioning.** Telemetry needs a rollup/purge policy or monthly partitions, or it will grow unbounded.
  - `offline_camera_ids` defaults to `'{}'::jsonb` (an empty **object**) but semantically holds a **list** — default should be `'[]'::jsonb`.
  - `Numeric()` columns have no precision/scale (unbounded). Usually fine, but pin them if you care about storage/validation.

### 🟡 `user_reports`, `report_status`, `messagedb`
- `user_reports` and `report_status` have a **`date_updated` column but no touch trigger** — it will silently stay equal to `date_created` (see cross-cutting item #2).
- `messagedb` has **no index on `topic`** and **no retention** — if it's an outbox/notification log it will need both.

---

## Cross-cutting issues (affect many tables)

These matter more than any single table.

**1. Timestamps are `TIMESTAMP WITHOUT TIME ZONE` + a database-level timezone.**
Every timestamp column is naive `DateTime`, and correctness depends on
`ALTER DATABASE gate_access SET timezone TO 'Africa/Accra'`. This is fragile in production:
DST/offset math, clients in other zones, and analytics tools all misread naive timestamps.
**Recommendation:** use `TIMESTAMPTZ` (`DateTime(timezone=True)`) and store UTC. This is the single
biggest portability/correctness improvement available.

**2. The `date_updated` touch trigger only covers the original 14 tables.**
The trigger loop in `11f328ef1746` was never extended. Tables added later that *have* a
`date_updated` column but **no** auto-update trigger:
`pending_users`, `pending_account_holders`, `personal_info_gate_links`,
`personal_info_privilege_links`, `user_reports`, `report_status`.
Their `date_updated` will never change. Either add triggers or drop the column where it's not used.

**3. Hardcoded database name.** `ALTER DATABASE gate_access ...` in `11f328ef1746` assumes the DB is
named `gate_access`. Deploying under any other name makes migration #2 fail. Parameterize it or set
the timezone at role/session level instead.

**4. Plaintext secrets.** OTPs and reset tokens (`users.reset_otp`, `account_holders.otp`,
`pending_users.otp`, `pending_account_holders.otp`) and `pending_users.password` are stored in the
clear. Hash them or give them short TTLs + cleanup.

**5. Trigger-based invariants have check-then-write races.** `enforce_max_attendees` and
`enforce_unique_user_per_estate` both `SELECT COUNT(...)` then allow the write. Under concurrency they
can both be violated. Where an invariant can be expressed as a unique/exclusion constraint, prefer that.

**6. Migration hygiene.** Roughly 8 migrations are empty no-ops
(`f6bdedc2948c`, `36ed554b7c83`, `0e00854b16fa`, `be7c59e5a456`, `dedb6f9a9056`, `c80cec97e68f`,
`9c48cc5584ed`, `24402f78d536`), three different files are all named *"added device_data column"*, and
`6afdaa634ca4` ("add last_alert **to gates**") actually adds `camera_alert_ts` **to system_metrics**.
Harmless to the running DB, but confusing. Not worth rewriting history — just know the names lie.

**7. `accesslog` NOT NULL back-fill risk.** `ef9f65dbce77` adds `gate_id INTEGER NOT NULL` with no
server default. If `accesslog` already held rows when this ran, the migration would have failed.
Confirm it applied cleanly in every environment; for future NOT-NULL additions, add a default or
back-fill first. Also, `accesslog` (a high-write table) has **no index on `license_plate_number` or
`timestamp`** and no retention policy.

---

## Suggested priority order

1. **Move OTP/reset/password columns off plaintext** (users, account_holders, both pending tables). *(security)*
2. **Add unique `(event_id, guest_id)` on `event_registers`.** *(data integrity, one-liner)*
3. **Add the missing `CHECK`/enum constraints** (event time ordering, `guests.status`, `logs.type`, `report_status.status`, `users` at-least-one-identifier). *(data integrity)*
4. **Fix the `date_updated` trigger coverage** for the 6 later tables, or drop the unused columns. *(consistency)*
5. **Give `system_metrics`, `accesslog`, `logs`, `messagedb` time-based indexes + a retention/partition plan.** *(scale)*
6. **Migrate timestamps to `TIMESTAMPTZ`** and remove the hardcoded-DB-name timezone hack. *(correctness/portability — larger effort, plan it deliberately)*
7. Decide whether the two capacity/uniqueness triggers need true concurrency safety. *(correctness under load)*

Items 2–4 are small and high-value; do them first. Item 6 is the largest but the most impactful for
long-term correctness.
