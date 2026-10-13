-- Deduplicate event_registers before adding UNIQUE (event_id, guest_id)
-- (migration d5ba08b18d68).
--
-- Keeps the earliest registration per (event_id, guest_id) -- lowest id --
-- and deletes the later redundant copies. Wrapped in a transaction and prints
-- what it removed. Review the SELECT output before committing in production;
-- change ROLLBACK to COMMIT (or run with -1 and no explicit txn) when satisfied.

BEGIN;

-- what will be removed
SELECT e.id, e.event_id, e.guest_id, e.date_created
FROM event_registers e
JOIN event_registers keep
  ON keep.event_id = e.event_id
 AND keep.guest_id = e.guest_id
 AND keep.id < e.id
ORDER BY e.event_id, e.guest_id, e.id;

DELETE FROM event_registers e
USING event_registers keep
WHERE keep.event_id = e.event_id
  AND keep.guest_id = e.guest_id
  AND keep.id < e.id;

-- confirm none remain
SELECT event_id, guest_id, count(*)
FROM event_registers
GROUP BY event_id, guest_id
HAVING count(*) > 1;

ROLLBACK;  -- <-- change to COMMIT once the output above looks right
