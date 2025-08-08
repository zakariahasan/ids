-- Detect bursts of port-scan alerts less than 30 s apart (SQLite ≥ 3.28)
WITH scans AS (
    SELECT
        alert_id,
        ts,
        src_ip,
        /* gap in seconds to the previous alert from the same src_ip */
        strftime('%s', ts) - LAG(strftime('%s', ts))
            OVER (PARTITION BY src_ip ORDER BY ts)  AS gap_sec
    FROM alerts
    WHERE alert_type = 'Port Scan'
),
clusters AS (
    SELECT
        *,
        /* start a new burst whenever gap is NULL or > 30 s */
        SUM(CASE
                WHEN gap_sec IS NULL OR gap_sec > 30 THEN 1
                ELSE 0
            END) OVER (PARTITION BY src_ip ORDER BY ts)  AS burst_id
    FROM scans
)
SELECT
    src_ip,
    MIN(ts)  AS burst_start,
    MAX(ts)  AS burst_end,
    COUNT(*) AS scans_in_burst
FROM clusters
GROUP BY src_ip, burst_id
HAVING COUNT(*) >= 3              -- only keep bursts ≥ 3 scans
ORDER BY scans_in_burst DESC;