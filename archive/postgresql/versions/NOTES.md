# Migration history notes

The chain is linear with a single head. A few revision **filenames and messages
are misleading** — the history is not worth rewriting, but know what these
actually do:

## No-op revisions (empty `upgrade`/`downgrade`)

These were created and left empty; they exist only to move the head pointer:

- `f6bdedc2948c` "true"
- `36ed554b7c83` "true"
- `0e00854b16fa` "true"
- `be7c59e5a456` "metricsupdate"
- `dedb6f9a9056` "metrics"
- `c80cec97e68f` "update metrics schema"
- `9c48cc5584ed` "add phone number to users for auth2"
- `24402f78d536` "added device_data column"

## Duplicated / misleading names

- Three separate files are all titled **"added device_data column"**:
  `4c3b28aafb71` (adds `gates.SNR` / `gates.RSSI`), `24402f78d536` (no-op),
  `48a59c16ecb6` (renames those to lowercase `snr` / `rssi`).
- `6afdaa634ca4` is titled **"add last_alert to gates"** but actually adds
  `camera_alert_ts` to **`system_metrics`**.
- `9c6b5726e200` "add last_alert_sent_at to gates" is the one that really adds
  `gates.last_alert_sent_at`.

## OTP column churn on `account_holders`

`otp` / `otp_generated_at` were added (`1b131ffa001b`), dropped (`395669e858f6`),
and re-added (`50dd30564d9b`). The column is String(255) as of `e231770546e7`.

## Hardcoded database name

`11f328ef1746` ran `ALTER DATABASE gate_access SET timezone TO 'Africa/Accra'`
with a literal name — it fails under any other database name. `f64ae7ce01ae`
resets it to UTC using `current_database()`; new deployments should not rely on
the database being named `gate_access`.

## Models vs migrations

`alembic/env.py` sets `target_metadata`, but every migration in this project is
hand-written — `alembic check` / autogenerate is **not** used and the ORM models
in `app/db/models/` are a lighter-weight view that has always lagged the
migrations (missing FK indexes, the `logs` SET NULL FKs, etc.). Treat the
migrations as the source of truth for the schema.
