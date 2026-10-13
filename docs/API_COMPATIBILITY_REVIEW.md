# API compatibility review — 2026-09-29

Compared this project's current MySQL baseline with `/Users/vdowana/gate-access-pg`.
The API is already converted to MySQL/PyMySQL despite its repository name.

**Result: static schema contracts now match, but joint deployment and existing-data
transfer are not yet validated.** No API code, deployed database, or records were
changed during this review.

## Remaining findings

### High: historical guest ownership needs an audit before transfer

API guest creation passes account_holder_id as guests.creator_id:
`/Users/vdowana/gate-access-pg/lambdas/guest/handlers/guest.py:112` and
`/Users/vdowana/gate-access-pg/lambdas/event_register/handlers/event_register.py:106`.
Guest reads and authorization also join it to account_holders.id (guest handler
line 435). The corrected MySQL foreign key now agrees with that API contract.

However, `scripts/transfer_ownership.py:16` treats each legacy creator_id as a
user ID, and line 23 resolves it through account_holders.user_id. Checking the
source foreign key to users.id (line 45) proves structural validity, not the
original writer's intent. If deployed historical code wrote account-holder IDs,
an accidentally matching user ID could have satisfied the old foreign key.
Automatic conversion could then assign a guest to the wrong owner, even if the
candidate appears unique and checksums pass. Current explicit overrides also
require the assumed source user, so they cannot resolve every such case.

This is a migration risk, not proof that any specific existing guest is wrong.
Before transfer, review the source guest rows against both interpretations, their
estates, and actual deployment history. Preserve already-correct account-holder
IDs where confirmed; convert genuine user IDs only with confirmed membership
mapping. The transfer needs an explicit validated source-ownership policy or
reviewed per-guest mapping supporting both cases. Do not run the current copy
command before that audit. No live source data was inspected during this review.

### High: supplied hosting configuration is not reachable from the Lambda API

`compose.yaml:11` publishes MySQL on 127.0.0.1 only. The API runs as Lambda
functions, and its VPC configuration is commented out in
`/Users/vdowana/gate-access-pg/template.yaml:43`.

The EC2 database needs a deliberately configured private network endpoint,
Lambda VPC connectivity, and narrowly scoped security groups, including access
for the deployment checker. A loopback URL or an SSH tunnel used on a developer
laptop is not a Lambda database endpoint. This is a deployment gap, not a schema
mismatch.

### High: API TLS requirements are not provisioned by the current EC2 guide

`/Users/vdowana/gate-access-pg/shared/python/database.py:87` enables certificate
and hostname verification by default. The supplied MySQL container has no
project-configured certificate for the production endpoint or shared trust setup.
Provision a trusted server certificate with matching hostname and make its CA
available to Lambda and the deployment checker where needed. Disabling TLS is
only a deliberate local-test setting; it is not the production resolution.

The API requires DATABASE_URL; it does not read this project's MYSQL_* variables.
It accepts mysql+pymysql and charset=utf8mb4, so URL syntax can match once the
endpoint, credentials, and TLS settings are configured.

### Medium: fresh-install privileges do not cover all API permission names

`scripts/seed.py:15` omits MANAGE_VEHICLES, MANAGE_SUB_USERS, and CREATE_SUB_USERS,
which are checked in `/Users/vdowana/gate-access-pg/shared/python/utils.py:295`
and lines 304–305. On a fresh install those specific permissions cannot be granted
until their privilege rows are created. Admin/MANAGE_ALL and other authorization
paths may still allow actions; this is not a claim that all such endpoints fail.

For the requested existing-data transfer, seed is intentionally skipped and
source privilege rows/assignments are preserved. Their actual coverage needs to
be checked with the imported data; this review did not query the source privileges.

## Confirmed matches

- guests.creator_id now references account_holders.id, matching both guest and
  event-registration insert paths and guest authorization joins.
- report_status.report_id is UNIQUE, matching the API's required unique-key
  checklist, submit_report insertion, and update_report_status's unique-key update
  (`lambdas/user/handlers/user.py:450`).
- Every table/column and unique key in scripts/check_database.py matches model
  metadata. This is a static comparison, not execution of that live checker.
- Users' UNIQUE expression indexes preserve the deleted_at-based reuse semantics;
  API queries filter soft-deleted users/memberships. Membership duplicate triggers
  raise MySQL 1062, matching the API's signup conflict handler (account.py:174).
- JSON object/list fields, UTC datetime storage, integer generated keys, string
  face IDs, and link-table keys match the API's SQL usage and driver conversions.
- The API's account updates reviewed do not move personal_info.estate_id, so the
  current estate-move guard does not conflict with those update paths.

## Checks actually executed

- API unit suite: **397 passed**, using the API's existing virtual environment,
  bytecode/cache writes disabled and temporary files directed to /tmp.
- Collected 300 SQL statements from the API's application SQL collector.
- Qualified all **197 SELECT/CTE statements** against the current schema using
  SQLGlot's MySQL dialect: no unresolved schema references.
- Checked **44 INSERT statements** for unknown columns and omitted required
  fields without database defaults: no mismatches. This cannot validate runtime
  parameter values, authorization, or server-side trigger execution.
- Compared the API's required-column and unique-key checklist: no mismatches.
- The latest database correction had **10 offline tests passed** and **4 live
  MySQL tests skipped**; those results are recorded in VALIDATION.md.

Docker still has no engine socket. No live migrations, API predeploy database
check, full handler integration test, or transfer rehearsal ran. Row-locking
triggers, concurrent signup/event registration, JSON queries, rollback, and real
TLS connections still require joint MySQL 8.4 acceptance tests.

The API repository's existing docs/mysql-compatibility-review.md describes the
older database state. Its guest foreign-key and report-status uniqueness findings
are resolved in the current files; its deployment concerns remain. Its previous
DDL-order unit-test failure has also been fixed here. That external report was
not edited as part of this comparison.
