-- Rolling 30-minute packet total with window functions for past 24 hours
-- Good for quick-trend dashboards without separate aggregation tables.
SELECT
    host_ip,
    interval_end,
    SUM(total_packets) OVER (
         PARTITION BY host_ip
         ORDER BY interval_end
         RANGE BETWEEN INTERVAL '30 minutes' PRECEDING AND CURRENT ROW
    ) AS pkts_last_30m
FROM   host_stats WHERE interval_end >= NOW() - INTERVAL '24 hour'
ORDER  BY host_ip, interval_end;