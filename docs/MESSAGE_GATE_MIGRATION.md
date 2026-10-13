# Gate-specific messages (mysql_0003)

`messagedb.gate_id` is a nullable, indexed foreign key to `gates.id`.
Existing messages stay intact with NULL gate_id; ownership is not inferred from
message text or a topic shared by multiple estates. Deleting a gate sets the
reference to NULL and preserves the message.

A message's estate is obtained through its gate. This avoids storing redundant
estate and gate IDs that could disagree. Because the estate is resolved through
the current gate record, moving a gate to another estate changes that derived
scope; applications should control estate reassignment.

## Deployment order

1. Back up MySQL. Upload `alembic/versions/mysql_0003_message_gate.py` and the
   updated model/transfer code to the database project on EC2.
2. In the database project's virtual environment, configure its TLS-enabled
   DATABASE_URL, then run `python -m alembic upgrade head` and
   `python -m alembic current`. Expect mysql_0003.
3. Deploy the changed heartbeat producer in the separate API project:
   `lambdas/heartbeat/handlers/gate.py` now inserts `(gate_id, topic, message)`
   using the gate's `device_id`. Deploy the migration first: the new INSERT
   cannot run against an old schema.
4. Verify new message rows carry the originating gate ID.

Do not repeat the data transfer for the deployed database. For future empty-target
transfers, the updated transfer script requires mysql_0003 and preserves old
PostgreSQL messages by setting the newly added gate_id to NULL.

## Delivery is a separate requirement

Adding the column does not send messages or enforce recipient selection. The
existing process_messages code in the API was commented out when reviewed, and
its old implementation selected all estates. Do not enable that old implementation.
The existing heartbeat entry point still imports the missing process_messages
function; that pre-existing API issue must be resolved before deploying that
handler. This change only modifies the producer's INSERT.

A dispatcher must restrict recipients to the message gate's estate, filter
memberships/users according to activation and deletion policy, and skip NULL
or missing gate references. Unknown ownership never means broadcast.

Read-only retrieval for an estate can use a bound parameter:

```sql
SELECT m.id, m.gate_id, m.topic, m.message, m.date_created
FROM messagedb m
JOIN gates g ON g.id = m.gate_id
WHERE g.estate_id = :estate_id
ORDER BY m.date_created, m.id;
```

The API must authorize the caller for :estate_id; accepting an arbitrary estate
parameter is not sufficient tenant isolation. INNER JOIN naturally excludes
messages with NULL gate_id, but the FK alone does not constrain delivery.

## Verification

The MySQL integration test checks legacy-message preservation through upgrade,
valid and invalid gate references, index creation, estate-specific joins,
SET NULL on gate deletion, and message preservation through downgrade/upgrade.
Downgrade removes gate associations, so it is not lossless for that new field.
