# Gate Access Database Project Requirements

Version: 1.0  
Date: 12 October 2026  
Status: Draft for stakeholder review  
Scope: Database foundation and integration contracts for the Gate Access system

## Purpose and business objectives

The Gate Access system supports controlled access to residential estates by maintaining users, estate memberships, guests, vehicles, gates, access schedules, events, operational messages, and device telemetry. Its database must keep these records consistent, preserve accountability, and support safe integration with the application and gate controllers.

This repository supplies the database foundation: SQLAlchemy models, Alembic migrations, business-rule triggers, seed data, schema exports, and PostgreSQL transfer tooling. It contains 25 application tables and targets MySQL 8.4. The HTTP API, user interfaces, authentication workflows, notification delivery, and physical gate control belong to separate components.

The primary objectives are to:

- Maintain reliable identities and estate memberships without duplicate live accounts.
- Store access permissions and schedules that application services can evaluate.
- Associate visitors and events with their responsible account holders.
- Prevent duplicate registrations and event overbooking during concurrent requests.
- Preserve operational evidence according to explicit deletion and retention policies.
- Scope gate messages to the correct estate and prevent accidental broadcasts.
- Support repeatable deployment and verified transfer of existing PostgreSQL records.

## Requirement conventions

Each requirement has a stable identifier for implementation and acceptance tracking. “Shall” describes required behavior. Priority **Must** means required for the relevant release; **Should** means desirable after the essential controls are satisfied.

The implementation column uses three classifications:

- **Present:** represented in current repository code; live acceptance still applies.
- **Integration:** requires behavior in an application, device service, or deployment environment outside this repository.
- **Gap:** requires a new policy, schema change, configuration, or implementation before it can be considered complete.

Requirements describing future behavior do not establish that the behavior already exists. This draft does not authorize deployment or a data cutover.

## Stakeholders and responsibilities

| Stakeholder | Responsibility |
| --- | --- |
| System owner | Approve scope, release criteria, retention, and operational targets. |
| Estate administrator | Manage estate memberships, gates, access groups, and permissions through the application. |
| Account holder | Maintain authorized visitors, vehicles, and events within permitted scope. |
| Security operator | Review access activity and gate health through authorized application views. |
| Application developer | Enforce authorization, input validation, transaction handling, and integration contracts. |
| Database maintainer | Manage schema versions, constraints, migrations, and transfer verification. |
| Operations team | Provide connectivity, secrets, TLS, backups, monitoring, and recovery procedures. |
| Tester | Verify database rules and complete end-to-end acceptance with the application and devices. |

These are responsibility categories, not additional account types stored in the schema. The fresh-install account types are ADMIN, USER_A, GUEST, and WORKER.

## Scope and boundaries

### Included capabilities

Identity storage, pending registrations, estate membership, estate and gate configuration, access groups and privileges, personal records, guests, face identifiers, vehicles, event registration, reports, access history, audit logs, gate messages, system metrics, soft deletion, database installation, and historical data transfer are included.

### External components

The application shall implement login, OTP issuance and verification, estate authorization, access decisions, notification dispatch, and report workflows. Gate services shall perform physical control and supply heartbeat, access, and telemetry data. Storing a face identifier does not implement facial recognition; storing a license plate does not implement plate recognition.

Mobile applications, dashboards, payment processing, recognition model training, hardware procurement, and ongoing PostgreSQL replication are outside the repository scope. They require separate requirements if added.

### Technical baseline

| Area | Required baseline |
| --- | --- |
| Runtime | Python 3.12 with dependencies from `requirements.txt`. |
| Database | MySQL 8.4, InnoDB; MariaDB and older MySQL releases are unsupported. |
| ORM and driver | SQLAlchemy with `mysql+pymysql`. |
| Schema lifecycle | Alembic active revisions; current head `mysql_0003`. |
| Character handling | `utf8mb4` with `utf8mb4_0900_bin`; identifier comparisons preserve case distinctions. |
| Transactions | READ COMMITTED for application writes. |
| Time storage | UTC `DATETIME(6)` and UTC database sessions. |
| Local deployment | Docker Compose with persistent MySQL volume and loopback binding. |
| Legacy import | PostgreSQL read access through the separate transfer dependencies. |

## Functional requirements

### Identity and registration

| ID | Requirement | Priority | Implementation |
| --- | --- | --- | --- |
| FR-01 | The database shall store users with an email, a phone number, or both; both identifiers cannot be NULL. | Must | Present |
| FR-02 | Each non-NULL email and phone number shall be unique among users whose `deleted_at` is NULL. Soft-deleted users shall release their identifiers for reuse. | Must | Present |
| FR-03 | User records shall store activation, administration, password, and password-reset data. Application services shall store password and OTP hashes and enforce OTP expiry and consumption. | Must | Present storage; Integration verification |
| FR-04 | Pending user records shall store a password, OTP, expiry, and optional email and phone identifiers, with uniqueness for each non-NULL identifier. The application shall require a usable identifier before registration. | Must | Present storage; Integration identifier validation |
| FR-05 | Pending account-holder records shall support invitation or approval data, house address, optional owner, OTP, and pending status. Promotion to a membership shall be transactional in the application. | Must | Present storage; Integration workflow |
| FR-06 | Restoring a soft-deleted user shall fail when its identifiers conflict with another live user. The application shall explain the conflict without exposing another user's private details. | Must | Present constraint; Integration response |

### Estates and memberships

| ID | Requirement | Priority | Implementation |
| --- | --- | --- | --- |
| FR-07 | Estate names and stored location-coordinate strings shall each be unique. The application shall validate coordinate syntax separately. | Must | Present uniqueness; Integration format validation |
| FR-08 | Creating an estate shall automatically create its REGULAR access group. | Must | Present trigger |
| FR-09 | Personal records shall belong to an estate and reference an account type and access group. Applications shall explicitly select the appropriate estate group rather than assume default group ID 1 is correct. | Must | Present references; Integration group selection |
| FR-10 | A user shall have at most one non-deleted account-holder membership per estate when the membership has a personal record. Concurrent insertion and update shall preserve this rule. | Must | Present triggers |
| FR-11 | A personal record referenced by an account holder shall not have its estate changed in place. Membership moves shall use a new personal record and validated reassignment. | Must | Present guard; Integration reassignment |
| FR-12 | Account holders shall support parent ownership for subaccounts. Hard deletion of a parent shall detach existing child memberships by setting their owner reference to NULL. | Must | Present |
| FR-13 | Normal user and membership removal shall use soft deletion when associated history must remain. Application queries shall exclude deleted records unless an authorized operation explicitly includes them. | Must | Present ORM support; Integration raw SQL and query policy |

Membership uniqueness uses deletion state, not the `is_active` flag. An inactive but non-deleted membership still occupies the user's membership for that estate. Memberships without `personal_info_id` bypass the estate uniqueness trigger; permitting them in production requires an explicit workflow decision.

### Gates and access permissions

| ID | Requirement | Priority | Implementation |
| --- | --- | --- | --- |
| FR-14 | Each gate shall belong to an estate and have a name unique within that estate, operating times, activation state, and heartbeat timestamp. | Must | Present |
| FR-15 | Access groups shall have names unique within their estate. Gate access-group links and personal gate links shall each store an opening and closing time without duplicate link pairs. | Must | Present |
| FR-16 | Privileges shall have unique names and be assignable through account-type and personal-record link tables. | Must | Present |
| FR-17 | The application shall authorize each access decision using the relevant estate, gate state, identity state, expiry, access schedule, and permission policy. | Must | Integration; policy decisions outstanding |
| FR-18 | The application shall reject cross-estate gate, personal-record, and access-group assignments, even when individual foreign keys are valid. | Must | Integration; Gap in database enforcement |
| FR-19 | Fresh-install privilege data shall cover the permission names required by the deployed API before permission-dependent workflows are accepted. | Must | Gap pending API contract reconciliation |

The database stores schedules but does not define their timezone, overnight behavior, or precedence between group and individual access. These decisions are required before FR-17 acceptance.

### Guests and vehicles

| ID | Requirement | Priority | Implementation |
| --- | --- | --- | --- |
| FR-20 | Guest records shall support a personal record, creator account-holder reference, status, and JSON metadata. `creator_id` shall reference `account_holders.id`, not `users.id`. | Must | Present |
| FR-21 | The application shall restrict guest management to authorized account holders and ensure consistent estate ownership. | Must | Integration |
| FR-22 | Face records shall have unique string identifiers of at most 64 characters and reference a guest. | Must | Present |
| FR-23 | Vehicles shall store a license plate, make, model, color, and optional personal-record reference. Plate numbers shall be indexed for lookup. | Must | Present |
| FR-24 | The application shall normalize plate inputs consistently and apply the approved rule for duplicate plates. No global plate uniqueness shall be assumed from the current schema. | Must | Integration; policy outstanding |

Guest status defaults to EXPECTED. Allowed status transitions and expiry behavior require an application policy; the current string column does not enforce an enumeration.

### Events and registration

| ID | Requirement | Priority | Implementation |
| --- | --- | --- | --- |
| FR-25 | Each event shall reference its creator account holder and store a name, attendee capacity, start time, and end time. End time shall be later than start time. | Must | Present |
| FR-26 | A guest shall be registered at most once for an event. | Must | Present unique constraint |
| FR-27 | New event registrations and moves to another event shall be rejected when the destination has no remaining capacity, including under concurrent writes. | Must | Present locking triggers |
| FR-28 | The application shall validate event capacity values and reject capacity reductions below existing registrations unless an approved reconciliation workflow is used. | Must | Integration; Gap in current database rules |
| FR-29 | The application shall validate guest eligibility, creator permissions, and estate compatibility before registration. | Must | Integration |

Current capacity enforcement counts registration records; it does not measure people physically present at an event. Direct updates to an event's capacity can currently lower it below the existing registration count.

### Reports and operational records

| ID | Requirement | Priority | Implementation |
| --- | --- | --- | --- |
| FR-30 | Users shall be able to submit reports containing a subject and description through an authorized application operation. | Must | Present storage; Integration submission |
| FR-31 | Each report shall have at most one current status row. Status changes shall update that row; the current model does not provide a status-history table. | Must | Present constraint; Integration workflow |
| FR-32 | Audit logs shall store event type, message, creation time, and optional estate, actor, account-holder, and plate references. Deleting referenced estates, users, or account holders shall set the relevant audit references to NULL and retain the log. | Must | Present |
| FR-33 | Access records shall store a plate number, event value, gate, and timestamp. Hard deletion of a gate shall follow the current cascade policy for its access records. | Must | Present |
| FR-34 | The application shall define and validate report statuses, audit types, and access event values before writing them. | Must | Integration; policy outstanding |

Audit logs and access records have different deletion behavior. A blanket claim that all operational history survives parent deletion would conflict with the current schema.

### Gate messages and telemetry

| ID | Requirement | Priority | Implementation |
| --- | --- | --- | --- |
| FR-35 | Messages shall store a topic, text body, UTC creation time, and optional gate reference. Gate deletion shall set the message reference to NULL and preserve its body. | Must | Present |
| FR-36 | Gate-originating producers shall include the actual gate ID. Historical unassigned messages shall remain unassigned unless ownership is independently verified. | Must | Integration; Present legacy transfer behavior |
| FR-37 | A dispatcher shall derive the estate from the message gate, authorize recipients within that estate, apply activation and deletion policies, and skip unassigned messages. Unknown ownership shall never cause a broadcast. | Must | Integration; delivery implementation outstanding |
| FR-38 | Notification delivery shall define retries, duplicate handling, and delivery evidence before dispatch is enabled. The current message table shall not be treated as proof of successful delivery. | Must | Gap |
| FR-39 | Each metric record shall reference a gate and store device and reception times, temperature, camera counts, storage values, service data, offline camera IDs, and optional camera alert time. | Must | Present |
| FR-40 | Ingestion services shall validate metric ranges and JSON shapes, including nonnegative counts and online camera counts no greater than total cameras. | Must | Integration; Gap in database checks |
| FR-41 | Monitoring services shall use the approved heartbeat and telemetry thresholds to identify faults and control repeated alerts. | Should | Integration; thresholds outstanding |

## Data requirements

### Entity inventory

| Domain | Tables | Main responsibility |
| --- | --- | --- |
| Identity and enrollment | `users`, `pending_users`, `account_holders`, `pending_account_holders` | Credentials, pending verification, estate memberships, and subaccount ownership. |
| Estate configuration | `estates`, `gates`, `access_groups`, `account_types`, `privileges` | Estates, access points, grouping, and permission vocabulary. |
| Personal and access assignments | `personal_info`, `personal_info_gate_links`, `gate_access_group_links`, `personal_info_privilege_links`, `account_type_privilege_links` | Estate identity, schedules, and privilege assignments. |
| Visitors and vehicles | `guests`, `faces`, `vehicles` | Visitor ownership, external face identifiers, and vehicle details. |
| Events | `events`, `event_registers` | Event details and capacity-controlled registration. |
| Reports | `user_reports`, `report_status` | User reports and current report status. |
| Operations | `logs`, `accesslog`, `messagedb`, `system_metrics` | Audit evidence, access events, messages, and telemetry. |

### Field limits and validation

| ID | Requirement | Current contract |
| --- | --- | --- |
| DR-01 | Application inputs shall respect declared string lengths and reject excessive input before persistence. | Examples: email 255, phone 20, plate 20, topic 100, report subject 255, face ID 64 characters. |
| DR-02 | Text fields shall have explicit application limits appropriate to their use. Excess input shall produce a validation error rather than silent truncation. | Message body, audit message, and report description use `Text`; a smaller business limit is not currently declared. Choose limits in the decision register. |
| DR-03 | JSON fields shall preserve native JSON values and enforce the shapes expected by consumers. | Guest metadata and running services default to `{}`; offline camera IDs default to `[]`. |
| DR-04 | Datetime inputs shall follow a UTC contract and preserve microseconds. | ORM aware inputs convert to UTC; naive inputs are treated as UTC; raw SQL clients must use UTC. |
| DR-05 | Time-of-day schedules shall have a documented interpretation. | Gate and link schedules use `TIME`; timezone and overnight rules remain undecided. |
| DR-06 | Identity normalization shall be consistent before uniqueness checks. | Binary collation preserves case distinctions; email, phone, plate, and coordinate normalization belong to application policy. |
| DR-07 | Precision shall be preserved for metric values. | Temperature uses `Numeric(6,3)` and storage values use `Numeric(12,3)`. |
| DR-08 | Foreign-key deletion policies shall be treated as part of the integration contract. | Consult model definitions and the student guide before allowing hard deletion. |

`nullable=False` prevents NULL, but does not by itself reject empty strings, whitespace-only values, malformed email addresses, or invalid coordinate strings. Applications shall validate these conditions where the workflow requires them.

### Retention and deletion

Users and account holders support soft deletion; the other tables do not have a general soft-delete mechanism. Hard deletion may cascade to related records and shall be limited to operations whose data consequences have been reviewed.

The supplied retention SQL removes pending users whose OTP expiry is more than seven days old and pending account holders still pending more than seven days after creation. It does not purge audit logs, access records, or metrics, and it does not itself schedule execution. Operations shall approve and schedule any cleanup policy before use. Production retention periods for messages, reports, telemetry, audit logs, access history, and soft-deleted identities remain to be decided.

## Integration requirements

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| IR-01 | Every application connection used for protected writes shall use READ COMMITTED and a UTC session. | Connection inspection and successful trigger-backed writes; incompatible isolation is rejected. |
| IR-02 | The application shall translate MySQL integrity and business-rule errors into stable domain responses and retry recoverable deadlocks with bounded attempts. | Duplicate, full-event, rollback, and deadlock scenarios produce documented outcomes. |
| IR-03 | Multi-record workflows shall use transactions so partial user promotion, registration, or ownership changes do not remain after failure. | Injected intermediate failure rolls back the workflow. |
| IR-04 | Application queries, including raw SQL, shall enforce estate authorization and deletion policy. Foreign keys alone shall not be considered tenant authorization. | A user authorized for one estate cannot read or modify another estate's records. |
| IR-05 | The database migration introducing a field shall be deployed before a producer begins writing that field. | `mysql_0003` is installed before gate-aware message inserts. |
| IR-06 | The deployed API and database shall agree on required tables, columns, privilege names, and foreign-key meanings. | Contract checks and representative end-to-end workflows pass. |

## Quality and operational requirements

| ID | Requirement | Priority | Verification |
| --- | --- | --- | --- |
| NFR-01 | Schema installation shall be repeatable through Alembic and include constraints, indexes, and business-rule triggers. `Base.metadata.create_all()` shall not be used as the installation path. | Must | Install on an empty disposable MySQL 8.4 database and inspect resulting objects. |
| NFR-02 | Migrations shall preserve existing records unless an explicitly reviewed transformation requires otherwise. Released schema changes shall use new revisions. | Must | Upgrade tests with representative existing rows. |
| NFR-03 | Production credentials shall be kept outside source control and separated by purpose. Runtime credentials shall have only the permissions needed by application operations. | Must | Secret configuration and database-grant review. |
| NFR-04 | Production database connections shall use TLS with certificate and hostname verification. | Must | Valid connection succeeds; untrusted certificate and wrong hostname fail. |
| NFR-05 | Production network access shall be limited to approved application and maintenance clients. Remote services shall have a configured private endpoint rather than rely on the local loopback binding. | Must | Connectivity from authorized clients succeeds; unauthorized clients cannot connect. |
| NFR-06 | Backups shall be encrypted, retained under an approved policy, and periodically restored to a separate environment. | Must | Successful restoration and recorded recovery timings. |
| NFR-07 | Monitoring shall cover availability, storage, connection exhaustion, slow queries, replication if configured, backup failures, and trigger/schema drift. | Must | Controlled fault exercises produce the expected alerts. |
| NFR-08 | Logs and diagnostics shall exclude passwords, OTPs, connection secrets, and unnecessary personal or biometric data. | Must | Representative application and maintenance output review. |
| NFR-09 | Common access, estate-log, message, and telemetry queries shall use suitable indexes and bounded result sets. | Must | Query-plan review and representative load test. |
| NFR-10 | Performance and recovery targets shall be measurable against an approved dataset and workload. | Must | Approved targets below and recorded benchmark/recovery results. |
| NFR-11 | Operational documentation shall describe deployment, rollback limits, trigger repair, data transfer, and destructive test isolation. | Must | Another maintainer completes a rehearsal using the guides. |

### Proposed service targets requiring approval

These targets are planning inputs, not measured capabilities or contractual commitments. Validate them against estate size, telemetry frequency, hardware, and operating budget before release.

| Measure | Proposed target | Measurement |
| --- | --- | --- |
| Database availability | 99.9% per calendar month | Successful connection and representative query probes against the production service; maintenance treatment must be agreed. |
| Common indexed reads | p95 at most 200 ms | Database query time under the approved representative workload; excludes network and API processing. |
| Membership and registration writes | p95 at most 500 ms | Committed transaction time under approved concurrency, including lock waits. |
| Recovery point objective | At most 24 hours of data loss | Verified usable backup age; tighter targets require an appropriate recovery design. |
| Recovery time objective | At most 4 hours | Time from recovery initiation to a restored, validated service. |

The load-test plan shall specify expected estate count, users per estate, simultaneous writes, access events per second, metric frequency, historical record volume, and growth horizon. The system owner shall approve these values; no capacity figure is implied by the current schema.

## Migration and deployment requirements

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| MR-01 | A new installation shall migrate an empty MySQL database before seeding. Seeding shall refuse application tables that already contain rows. | Fresh installation succeeds; seed refuses a populated database. |
| MR-02 | A transfer target shall be empty, migrated to `mysql_0003`, and kept inaccessible to application writers. It shall not be seeded before import. | Preflight verifies revision and emptiness. |
| MR-03 | Transfer preflight shall detect missing or unexpected source structure, duplicate memberships, conflicting report statuses, and unresolved guest ownership. | Invalid fixtures are refused before copy. |
| MR-04 | Historical guest ownership shall be audited against actual writer behavior before conversion. A legacy foreign key alone shall not establish whether the stored number meant a user ID or account-holder ID. | Reviewed ownership interpretation and mappings; ambiguous rows block cutover. |
| MR-05 | Transfer shall preserve IDs, hashes, JSON, timestamps, deletion state, and relationships except approved ownership transformations and NULL gate assignment for legacy messages. | Per-table counts and transformed SHA-256 digests match. |
| MR-06 | All source writers shall remain stopped during final snapshot copy and cutover. PostgreSQL shall remain intact until acceptance. | Writer freeze and restoration of the source backup are verified. |
| MR-07 | Trigger suspension during transfer shall be followed by verified restoration before the target is released. Interrupted restoration shall use the documented recovery procedure. | Required triggers exist and business-rule tests pass after transfer. |
| MR-08 | Rollback shall account for writes accepted after cutover. Switching back to PostgreSQL after new MySQL writes shall require reconciliation of those changes. | Rehearsed rollback plan identifies the reconciliation method and responsible operator. |

Current ownership tooling assumes source guest creator values are user IDs and validates that interpretation. The API compatibility review identifies a historical ambiguity that the existing override mechanism may not resolve. MR-04 must be settled before running a production copy; an audited interpretation may require a tooling change.

MySQL DDL auto-commits. A failed migration may leave partial schema changes, so recovery shall inspect the actual schema and migration state. Recreating a target is appropriate only for a confirmed disposable empty database, never a populated production or imported target.

## Acceptance criteria

Acceptance requires database checks and integration evidence. Offline schema checks alone cannot establish live trigger correctness, network readiness, notification delivery, or physical gate behavior.

| Scenario | Expected result | Requirements |
| --- | --- | --- |
| User has neither identifier | Database rejects the row; application returns a validation response. | FR-01 |
| Duplicate live identifier and identifier reuse | Duplicate is rejected; reuse after soft deletion succeeds; conflicting restoration is rejected. | FR-02, FR-06 |
| Estate creation | Exactly one REGULAR group is created by the insertion workflow. | FR-08 |
| Two concurrent memberships for one user and estate | At most one non-deleted membership commits, including when different personal records are used. | FR-10, IR-01 |
| Personal record estate change | Change is rejected when an account-holder reference exists. | FR-11 |
| Cross-estate operation | Caller cannot assign or access records in an unauthorized estate. | FR-18, IR-04 |
| Event registration duplicate | Second registration for the same event and guest is rejected. | FR-26 |
| Concurrent competition for the last event place | Only one registration commits; capacity is not exceeded. | FR-27 |
| Full-event registration move | Move is rejected and the original registration remains intact. | FR-27, IR-03 |
| Report status update | Existing status changes without creating a second row. | FR-31 |
| Parent deletion | Audit references become NULL; gate messages survive; access and metric cascades match declared policy. | FR-32, FR-33, FR-35 |
| Scoped gate message | Only eligible recipients in the originating estate are selected; NULL-gate messages are skipped. | FR-36, FR-37 |
| Message retry | Approved duplicate handling and delivery evidence behave as specified. | FR-38 |
| UTC conversion | A timezone-aware input round-trips to the equivalent UTC instant with microsecond precision. | DR-04 |
| Invalid input boundaries | Oversized text, invalid ranges, invalid JSON shapes, and empty required business values receive validation errors. | DR-01, DR-02, FR-40 |
| Legacy transfer | Counts, digests, audited ownership, message gate NULLs, and restored triggers are verified. | MR-03 through MR-07 |
| Backup restoration | A separate environment restores successfully within approved recovery objectives. | NFR-06, NFR-10 |
| Production application connection | Private connectivity, certificate validation, schema contract, and actual workflows succeed. | NFR-04, NFR-05, IR-06 |

### Verification procedure

1. Run `python -m unittest discover -s tests -v` for the repository checks. Record skips separately from passes.
2. Generate the Alembic SQL for review and confirm there is one active head.
3. Run the live suite only against a new disposable database whose name starts with `gate_access_test`, using the documented `DATABASE_URL` and `TEST_DATABASE_URL` safeguards.
4. Rehearse a migration and, if applicable, a legacy transfer on isolated copies.
5. Complete application tests for authentication, memberships, visitors, events, reports, messages, and access decisions.
6. Complete production-equivalent TLS, network, backup restoration, and load tests.
7. Obtain acceptance from the system owner, application maintainer, and operations owner against the release scope.

No production database shall be used for destructive integration tests. Historical validation reports retain their original dates and results; their earlier revision numbers and test totals are not current release acceptance evidence.

## Decisions required before production acceptance

| ID | Decision | Responsible role | Consequence |
| --- | --- | --- | --- |
| DEC-01 | Maximum message, audit-message, report-description, and JSON payload sizes; character versus byte limits. | System owner and application developer | Required for consistent validation and boundary testing. |
| DEC-02 | Gate schedule timezone, overnight windows, and precedence of personal versus group schedules. | Estate operations and application developer | Required for deterministic access decisions. |
| DEC-03 | Email, phone, plate, and coordinate normalization; whether and where plates must be unique. | System owner and application developer | Required to avoid inconsistent identity and vehicle matching. |
| DEC-04 | Guest statuses, report statuses, access event values, transitions, and expiry rules. | System owner | Required for validated workflows. |
| DEC-05 | Whether incomplete memberships and guests without owners or personal records are permitted. | System owner | Required to close nullable-reference workflow gaps. |
| DEC-06 | Recipient eligibility, channel, delivery timing, retries, duplicate handling, and dispatch evidence. | System owner and application developer | Required before message dispatch is enabled. |
| DEC-07 | Historical guest creator interpretation and reviewed mappings. | Data owner and database maintainer | Blocks production transfer until resolved. |
| DEC-08 | Retention and erasure periods for each data category, including face identifiers and backups. | System owner and operations | Required before cleanup and hard deletion policies are enabled. |
| DEC-09 | Production topology, certificates, runtime privileges, backup strategy, workload, and service targets. | Operations and system owner | Required for deployment and operational acceptance. |
| DEC-10 | Complete privilege vocabulary and fresh-install assignments matching the deployed API. | Application and database maintainers | Required for permission-dependent acceptance. |
| DEC-11 | Whether gates may move between estates and how historical message scope should behave. | System owner and application developer | Gate reassignment changes a message's derived estate in the current model. |

## Delivery sequence

1. **Database baseline:** verify schema, triggers, UTC behavior, constraints, and fresh installation on MySQL 8.4.
2. **Integration contracts:** resolve access policies, field limits, permissions, status values, and application transaction behavior.
3. **Production preparation:** configure private connectivity, TLS, credentials, monitoring, and tested backups.
4. **Migration rehearsal:** audit guest ownership, test transfer and recovery, and record verification evidence if legacy data is in scope.
5. **Acceptance and release:** complete end-to-end and load tests, resolve release-blocking decisions, and follow the approved cutover plan.

## Supporting project references

- [Project setup and checks](../README.md)
- [Database table and design guide](DATABASE_STUDENT_GUIDE.md)
- [Gate message migration and delivery boundaries](MESSAGE_GATE_MIGRATION.md)
- [PostgreSQL transfer procedure](MYSQL_MIGRATION.md)
- [API compatibility findings](API_COMPATIBILITY_REVIEW.md)
- [Historical conversion validation](VALIDATION.md)
- [EC2 hosting procedure](EC2_MYSQL_HOSTING.md)
- [Trigger repair procedure](TRIGGER_REPAIR.md)
- [Current models](../app/db/models/)
- [Trigger definitions](../scripts/schema_rules.py)
- [Active migrations](../alembic/versions/)
- [Automated checks](../tests/)
