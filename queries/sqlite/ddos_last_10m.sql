-- Requires SQLite 3.28+ (window functions) and 3.30+ if you want FILTER
SELECT
    ts,
    -- count only rows whose alert_type = 'DDoS' in the 10-minute window
    COUNT(CASE WHEN alert_type = 'DDoS' THEN 1 END) OVER (
        -- use the timestamp (converted to Unix-epoch seconds) for ordering
        ORDER BY strftime('%s', ts)
        RANGE BETWEEN 600 PRECEDING AND CURRENT ROW   -- 600 s = 10 min
    ) AS ddos_window
FROM alerts
ORDER BY ts;
