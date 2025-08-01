WITH scans AS (
    SELECT alert_id, ts, src_ip,
           ts - LAG(ts) OVER (PARTITION BY src_ip ORDER BY ts) AS gap
    FROM   alerts
    WHERE  alert_type = 'Port Scan'
),
clusters AS (
    SELECT *,
           SUM(CASE WHEN gap IS NULL OR gap > INTERVAL '30 seconds' THEN 1 ELSE 0 END)
           OVER (PARTITION BY src_ip ORDER BY ts) AS burst_id
    FROM   scans
)
SELECT src_ip,
       MIN(ts) AS burst_start,
       MAX(ts) AS burst_end,
       COUNT(*) AS scans_in_burst
FROM   clusters
GROUP  BY src_ip, burst_id
HAVING COUNT(*) >= 3
ORDER  BY scans_in_burst DESC;