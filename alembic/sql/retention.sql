-- Run manually or with your scheduler, only after reviewing retention policy.
-- Audit and telemetry tables (logs, accesslog, system_metrics) are never purged here.
SET time_zone = '+00:00';
DELETE FROM pending_users WHERE otp_expiry < UTC_TIMESTAMP(6) - INTERVAL 7 DAY;
DELETE FROM pending_account_holders
WHERE is_pending = TRUE AND date_created < UTC_TIMESTAMP(6) - INTERVAL 7 DAY;
