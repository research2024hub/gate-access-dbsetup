-- Review only: MySQL baseline already prevents duplicates.
START TRANSACTION;
SELECT DISTINCT e.id, e.event_id, e.guest_id FROM event_registers e
JOIN event_registers earlier ON earlier.event_id=e.event_id
AND earlier.guest_id=e.guest_id AND earlier.id<e.id;
DELETE e FROM event_registers e JOIN event_registers earlier
ON earlier.event_id=e.event_id AND earlier.guest_id=e.guest_id AND earlier.id<e.id;
ROLLBACK;
