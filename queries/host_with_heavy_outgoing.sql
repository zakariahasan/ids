-- Hosts with heavy outgoing bias
-- Flags hosts whose outgoing traffic is ≥ double their incoming traffic over the past hour.

WITH last_hour AS (
    SELECT host_ip,
           SUM(incoming_packets) AS in_pkts,
           SUM(outgoing_packets) AS out_pkts
    FROM   host_stats
    WHERE  interval_end >= NOW() - INTERVAL '2 hour'
    GROUP  BY host_ip
)
SELECT host_ip,
       in_pkts,
       out_pkts,
       COALESCE((ROUND(out_pkts::NUMERIC / NULLIF(in_pkts,0),2)),0) AS out_in_ratio
FROM   last_hour
WHERE  out_pkts >= 1 * in_pkts         -- tweak ratio as needed
ORDER  BY out_in_ratio DESC;