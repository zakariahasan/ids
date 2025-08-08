-- Rolling 30-minute packet total with window functions for past 24 hours
-- Good for quick-trend dashboards without separate aggregation tables.
-- Rolling 30-minute packet total per host (SQLite ≥ 3.28)
SELECT
    host_ip,
    interval_end,
    SUM(total_packets) OVER (
        PARTITION BY host_ip
        ORDER BY CAST(strftime('%s', interval_end) AS INTEGER)
        RANGE BETWEEN 1800 PRECEDING  -- 1 800 s = 30 min
              AND     CURRENT ROW
    ) AS pkts_last_30m
FROM host_stats
WHERE interval_end >= datetime('now', '-24 hours')
ORDER BY host_ip, interval_end;
