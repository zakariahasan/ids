-- Hosts with heavy outgoing bias
-- Flags hosts whose outgoing traffic is ≥ double their incoming traffic over the past hour.

-- Hosts whose outgoing traffic ≥ incoming traffic in the past 2 hours (SQLite)
WITH last_two_hours AS (
    SELECT host_ip,
           SUM(incoming_packets) AS in_pkts,
           SUM(outgoing_packets) AS out_pkts
    FROM host_stats
    WHERE interval_end >= datetime('now', '-20 hours')
    GROUP BY host_ip
)
SELECT host_ip,
       in_pkts,
       out_pkts,
       COALESCE(ROUND(out_pkts / NULLIF(in_pkts, 0), 2), 0) AS out_in_ratio
FROM last_two_hours
WHERE out_pkts >= in_pkts       -- tweak ratio threshold here
ORDER BY out_in_ratio DESC;
