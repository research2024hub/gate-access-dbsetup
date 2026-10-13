# Conversion validation — 2026-09-29

Completed:

- All 25 SQLAlchemy tables compile as MySQL DDL.
- Frozen baseline tables, indexes, and trigger definitions match the models.
- Alembic has one head, `mysql_0001`; offline upgrade SQL generation succeeds.
- Ten offline tests pass, including schema constraints, original user/membership
  columns, UTC conversion, guest ownership resolution, duplicate-report preflight,
  and checksum verification after ownership conversion.
- Python compilation, installed dependency checks, and Compose configuration pass.
- Read-only PostgreSQL inspection found all 25 expected tables, matching original
  columns, and no extra application tables. Row counts totaled 212,757 during
  inspection (live data may change). No record values or credentials were logged.

Not yet completed:

- Live MySQL migration, trigger, and concurrency tests. Docker Desktop did not
  provide an engine socket, so the integration test is skipped, not passed.
- PostgreSQL-to-MySQL data copy and checksum verification.
- Application acceptance tests and cutover (backend code is outside this folder).
- AWS provisioning/deployment. The EC2 guide is prepared; no AWS resources created.

No PostgreSQL records were modified. SOURCE_DATABASE_URL in the private .env
preserves the original connection; MYSQL_* describes the new local target.
Start Docker Desktop's engine to continue live validation. Freeze source writers
and take a database backup before the final copy/cutover.

## Uniqueness revision

Removed all four visible helper columns from users and account_holders. User
email/phone uniqueness now uses MySQL UNIQUE expression indexes. Account-holder
uniqueness uses locking triggers over the original columns; source preflight
checks the same user/estate rule. Both preserve soft-delete reuse. The undeployed
baseline and SQL export were regenerated. Live tests for these rules remain
pending Docker availability; offline checks are not a substitute for them.

## Guest ownership and report status correction

- guests.creator_id references account_holders.id; report_status.report_id has a
  UNIQUE constraint in the models, undeployed mysql_0001 baseline, and SQL export.
- Transfer preflight resolves user IDs to account-holder IDs using estate context,
  supports validated explicit choices for ambiguous owners, and refuses duplicate
  report statuses. Source data is not edited. Guest checksums verify mapped owners.
- Ten offline tests passed; four live MySQL integration tests are skipped until
  a disposable MySQL test database is available. No database migration or record
  transfer was executed for this correction.
