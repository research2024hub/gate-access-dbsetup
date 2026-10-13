-- Retention / cleanup jobs.
--
-- These are NOT migrations. Schedule them with pg_cron, an application cron, or
-- an external scheduler (e.g. EventBridge -> a small Lambda).
--
-- PRODUCT DECISION (2026-09-01): the audit / telemetry tables --
--   system_metrics, accesslog, logs -- are RETAINED INDEFINITELY and must
--   never be purged. When their volume starts to hurt query or backup times,
--   the answer is native range partitioning (by month) so old data can be
--   detached to cheaper storage or a data lake -- still no DELETE. That work is
--   tracked separately.
--
-- Only the ephemeral signup tables are cleaned up here.

-- ---------------------------------------------------------------------------
-- Ephemeral signup tables: rows for abandoned / completed signups.
-- Safe to delete -- a real account is created in `users` / `account_holders`;
-- the pending row is scratch space that is otherwise never removed.
-- ---------------------------------------------------------------------------

-- Registrations that were never verified (OTP long expired).
DELETE FROM pending_users
WHERE otp_expiry < now() - interval '7 days';

-- Sub-account invites that were never accepted.
DELETE FROM pending_account_holders
WHERE is_pending
  AND date_created < now() - interval '7 days';

-- messagedb (notification / status outbox): retention is undecided. If it is
-- treated as audit, leave it alone and partition later like the tables above;
-- if it is a transient outbox, uncomment and tune:
-- DELETE FROM messagedb WHERE date_created < now() - interval '90 days';

-- ---------------------------------------------------------------------------
-- Example pg_cron registration (run once, as a superuser, in the target DB).
-- First run may hit a large backlog -- do that once by hand in LIMIT-batched
-- loops before scheduling the nightly job.
-- ---------------------------------------------------------------------------
-- SELECT cron.schedule('purge-pending-users', '15 3 * * *',
--   $$DELETE FROM pending_users WHERE otp_expiry < now() - interval '7 days'$$);
-- SELECT cron.schedule('purge-pending-account-holders', '20 3 * * *',
--   $$DELETE FROM pending_account_holders
--     WHERE is_pending AND date_created < now() - interval '7 days'$$);
