SELECT
    -- Round each timestamp down to the start of its hour
    strftime('%Y-%m-%d %H:00:00', ts) AS hour_bucket,
    alert_type,
    COUNT(*) AS alert_cnt
FROM alerts
-- Only include the past 24 hours
WHERE ts >= datetime('now', '-36 hours')
GROUP BY hour_bucket, alert_type
ORDER BY hour_bucket, alert_type;
