# Transfer PostgreSQL records to MySQL

The conversion changes the project code. It does not convert an existing
PostgreSQL server in place. The earlier Downloads folder backup contains files,
not the database server's records. Keep PostgreSQL intact throughout cutover.

## Before copying

1. Take a PostgreSQL database backup using your database provider's snapshot
   facility or `pg_dump` (custom format). Verify it can be restored. Do not put a
   password directly in shell history; use PostgreSQL's password prompt or a
   permission-restricted `.pgpass` file.
2. Prepare a separate MySQL 8.4 instance, with enough storage for the full source,
   indexes, and backups. Use the supplied Compose setup or the EC2 guide.
3. Set `SOURCE_DATABASE_URL` to the original PostgreSQL URL and `MYSQL_*` to the
   new target in `.env`. The working-copy conversion already preserves the original
   URL. `DATABASE_URL`, if set in your shell, overrides `MYSQL_*`; remove an old
   exported PostgreSQL `DATABASE_URL` from the shell before running this project.
4. Install transfer dependencies and create the **empty** schema:

   ```bash
   python -m pip install -r requirements-transfer.txt
   python -m alembic upgrade head
   python -m scripts.transfer_postgres --check
   ```

The preflight reads PostgreSQL through a repeatable-read, read-only transaction,
requires all 25 expected tables and columns, and refuses a nonempty target. It
reports table row counts. Extra source tables/columns cause a refusal so records
cannot silently be omitted; reconcile the schema before proceeding. Read access
is needed on every source table. Do not run `scripts.seed` on this target.

## Guest ownership and report-status preflight

The target requires guests.creator_id to reference account_holders.id and allows
at most one report_status row per report_id. The source still uses user IDs for
guest ownership; changing the foreign key alone would assign incorrect owners.

The transfer matches the old creator user with an account holder in the guest's
estate (from the guest's personal_info). If the guest has no estate, the source
user must have exactly one membership overall. Soft-deleted memberships remain
candidates so historical ownership is not silently reassigned to a newer account.
A NULL creator stays NULL. Missing or multiple candidates stop preflight.

The current transfer code requires target revision `mysql_0003`. PostgreSQL
`messagedb` rows without the newly added `gate_id` are copied with `gate_id=NULL`;
no gate ownership is inferred. NULL does not mean broadcast: message delivery
must skip unassigned messages. See [the message migration guide](MESSAGE_GATE_MIGRATION.md).

For an ambiguous guest, supply a reviewed JSON mapping of guest ID to account-holder
ID, for example `{"12": 91}` in a private file. The tool checks that each selected
membership belongs to the original user and, where known, the guest's estate:

```bash
python -m scripts.transfer_postgres --check --guest-owner-map /private/path/guest-owners.json
python -m scripts.transfer_postgres --copy --guest-owner-map /private/path/guest-owners.json
```

Multiple status rows for one report also stop preflight; the tool never chooses
or deletes a status automatically. Reconcile these records explicitly before
transfer. No source data is modified by either transfer command.

The backend must now write account-holder IDs into guests.creator_id, and update
an existing report_status row when changing a report's status. Inserting another
status for the same report will fail. Guest deletion still uses ON DELETE CASCADE,
now from account_holders rather than directly from users.

## Final copy and verification

1. Stop every source writer: the backend, workers, scheduled jobs, and gate/device
   consumers. Leave PostgreSQL running so it can be read.
2. Keep the new target inaccessible to applications during transfer.
3. Run:

   ```bash
   python -m scripts.transfer_postgres --copy
   ```

The tool preserves primary IDs, password hashes, JSON, timestamps, and soft-deleted
records. Guest creator_id is deliberately converted from a user ID to the
corresponding account-holder ID. Other foreign-key values are preserved. Self-referencing account owners are linked after their parent
rows exist. It inserts explicit IDs; MySQL advances AUTO_INCREMENT accordingly.
It checks per-table row counts and SHA-256 digests before committing. For guests,
the expected digest uses the mapped creator_id; every other value must match the
source. Schema constraints validate foreign keys, identifiers, and event time
ranges. All application columns are included in this comparison.

Source writes after the snapshot are **not** copied: this is an offline cutover,
not ongoing replication. Keep writers stopped until the switch is complete.

MySQL triggers are temporarily removed to prevent estate initialization from
creating duplicate access groups and to preserve original timestamps. They are
restored in a `finally` block. Data insertion is one InnoDB transaction; errors
roll it back. A process/server crash can interrupt trigger restoration. Keep the
target offline and run:

```bash
python -m scripts.transfer_postgres --restore-triggers
```

Then inspect whether the data transaction committed; do not blindly rerun a copy
against a populated target. A failed trigger restoration must be fixed before use.
For a very large source, plan the time and disk/undo space for this transaction;
perform a rehearsal first. Trigger business rules are not applied retroactively
to copied historical rows; review any pre-existing capacity violations.

4. Test login, memberships, guest registration, device messages, and reports in
   the actual backend. That backend is not in this folder and may contain its own
   PostgreSQL-specific SQL and exception handling.
5. Point that backend at MySQL, deploy matching models/driver changes, and restart
   writers. MySQL integrity errors have different codes from PostgreSQL errors.
6. Take a MySQL backup and keep PostgreSQL read-only until acceptance. Before new
   MySQL writes, rollback means pointing the backend back at PostgreSQL. After new
   writes, switching back without reconciling them would lose changes.

## Behavior changes and preserved rules

- JSONB becomes MySQL JSON; object/list values are retained. Offline camera IDs
  default to `[]` on new rows; service status and guest metadata default to `{}`.
- Datetimes use `DATETIME(6)` in UTC. ORM bindings convert aware inputs to UTC and
  return UTC-aware datetimes; naive inputs are interpreted as UTC. Raw SQL clients
  must also use UTC. Connections set the session timezone to `+00:00`.
- Case-sensitive `utf8mb4_0900_bin` preserves distinct case/accent values in unique
  identifiers. Test actual application searches rather than assuming MySQL's usual
  case-insensitive defaults.
- UNIQUE expression indexes replace PostgreSQL partial unique indexes for users.
  No visible helper columns are added: emails/phones are indexed only when
  deleted_at is NULL. MySQL internally implements functional indexes with hidden
  generated columns. Deleted users release their email/phone; restoring a
  conflicting row fails.
- Account membership uniqueness is enforced by INSERT/UPDATE triggers using the
  original user_id and personal_info_id columns. They lock the user row and check
  for another non-deleted membership in the same estate with a locking read.
  No estate/helper columns are added to account_holders. The transfer preflight
  also checks for duplicate memberships because triggers are disabled during copy.
  A personal_info row with account memberships cannot be moved to another estate
  in place: create a new personal record and reassign the membership.
- Registration capacity uses event row locks and locking reads rather than
  PostgreSQL advisory locks. Both inserts and moves between events are checked.
  Applications should retry transactions after deadlocks, as with other InnoDB
  transactions. Direct changes to an event's capacity can still lower it below
  current attendance, matching the old behavior.
- Estate inserts create a REGULAR access group; date_updated triggers also cover
  raw SQL writes. The personal_info default access_group_id remains 1 for
  compatibility; applications should supply the correct group for the estate.
- Audit log foreign keys use SET NULL; soft deletion remains available for users
  and memberships. Existing cascade policies on other tables are preserved.

Original PostgreSQL artifacts are archived, not executable MySQL migrations.
A MySQL baseline must never be stamped over a PostgreSQL database.

References: [MySQL generated columns](https://dev.mysql.com/doc/refman/8.4/en/create-table-generated-columns.html),
[MySQL JSON](https://dev.mysql.com/doc/refman/8.4/en/json.html),
[foreign-key behavior](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html).

UNIQUE expression index reference: [MySQL CREATE INDEX](https://dev.mysql.com/doc/refman/8.4/en/create-index.html).
