--  New-source spike – possible DDoS precursor
-- Find intervals where a host suddenly sees traffic from 5+ new source IPs compared to the previous interval for past 12 hours

-- New-source spike (SQLite ≥ 3.28 for LAG)
WITH ranked AS (
    SELECT
        stats_id,
        host_ip,
        interval_start,
        unique_src_ips,
        LAG(unique_src_ips) OVER (
            PARTITION BY host_ip
            ORDER BY interval_start
        ) AS prev_src_ips
    FROM host_stats
    WHERE interval_end >= datetime('now', '-12 hours')
)
SELECT
    host_ip,
    interval_start,
    unique_src_ips,
    prev_src_ips,
    (unique_src_ips - prev_src_ips) AS new_src_jump
FROM ranked
WHERE prev_src_ips IS NOT NULL
  AND (unique_src_ips - prev_src_ips) >= 2   -- spike threshold
ORDER BY new_src_jump DESC;
