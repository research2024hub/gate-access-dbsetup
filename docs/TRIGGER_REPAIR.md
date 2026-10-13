# mysql_0002 trigger repair

The deployed mysql_0001 membership and capacity triggers issue locking reads on
 their own triggering tables and fail with MySQL error 1442. mysql_0002 replaces
only those four triggers. It does not change tables or application records.

The parent user/event locks remain. Counts use nonlocking reads with READ
COMMITTED isolation. Guard clauses reject sessions configured with another
isolation level. All writers must use READ COMMITTED; do not override individual
transactions to a different isolation level. Existing connections may need
reconnecting after changing server defaults.

Before deployment, back up the database and pause all application writes.
Upload alembic/versions/mysql_0002_fix_trigger_locking.py,
scripts/schema_rules.py and scripts/transfer_postgres.py. Keep mysql_0001 intact.
Use a TLS-enabled SQLAlchemy DATABASE_URL for Alembic, with the local CA path
and ssl_check_hostname=true. Run `python -m alembic upgrade head`, followed by
`python -m alembic current`; expect mysql_0002.

MySQL DDL auto-commits. Keep writes paused if deployment fails. The migration
uses DROP TRIGGER IF EXISTS and may be rerun to complete a partial application.
Do not stamp the revision manually. Downgrade reinstalls the original faulty
triggers, so it is not a way to restore working application writes.

Verification: 20 tests passed against disposable MySQL 8.4, including concurrent
membership creation, concurrent event capacity, event movement, membership
updates, soft delete and restoration, rejection of REPEATABLE READ sessions,
and preservation of application records across trigger downgrade/upgrade.
These tests do not constitute a production deployment or a Lambda network test.
