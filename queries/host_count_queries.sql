
-- Top “talkers” by bandwidth in the last 10 minutes
-- Shows which hosts moved the most bytes recently.
SELECT
    host_ip,
    SUM(total_packets_size)        AS bytes_last_10m,
    SUM(total_packets)             AS pkts_last_10m
FROM   host_stats
WHERE  interval_end >= NOW() - INTERVAL '100000 minutes'
GROUP  BY host_ip
ORDER  BY bytes_last_10m DESC
LIMIT  5;

--Average packet size per host (all time)
--Useful for spotting hosts that send many small probes vs. large data bursts.
SELECT
    host_ip,
    SUM(total_packets_size)::NUMERIC / NULLIF(SUM(total_packets),0) AS avg_pkt_size_bytes,
    SUM(total_packets)                                              AS total_pkts
FROM   host_stats
GROUP  BY host_ip
ORDER  BY avg_pkt_size_bytes DESC;


-- Hosts with heavy outgoing bias
-- Flags hosts whose outgoing traffic is ≥ double their incoming traffic over the past hour.

WITH last_hour AS (
    SELECT host_ip,
           SUM(incoming_packets) AS in_pkts,
           SUM(outgoing_packets) AS out_pkts
    FROM   host_stats
    WHERE  interval_end >= NOW() - INTERVAL '1 hour'
    GROUP  BY host_ip
)
SELECT host_ip,
       in_pkts,
       out_pkts,
       ROUND(out_pkts::NUMERIC / NULLIF(in_pkts,0),2) AS out_in_ratio
FROM   last_hour
WHERE  out_pkts >= 2 * in_pkts         -- tweak ratio as needed
ORDER  BY out_in_ratio DESC;

-- “Port-fan-out” check – many destination ports hit
-- Large unique_dst_ports counts can indicate port scanning or very chatty services.
SELECT
    interval_start,
    interval_end,
    host_ip,
    unique_dst_ports
FROM   host_stats
WHERE  unique_dst_ports >= 10          -- threshold; adjust for your baseline
ORDER  BY unique_dst_ports DESC;


--  New-source spike – possible DDoS precursor
-- Find intervals where a host suddenly sees traffic from 5+ new source IPs compared to the previous interval.

WITH ranked AS (
    SELECT
        stats_id,
        host_ip,
        interval_start,
        unique_src_ips,
        LAG(unique_src_ips) OVER (PARTITION BY host_ip ORDER BY interval_start) AS prev_src_ips
    FROM host_stats
)
SELECT
    host_ip,
    interval_start,
    unique_src_ips,
    prev_src_ips,
    (unique_src_ips - prev_src_ips) AS new_src_jump
FROM   ranked
WHERE  prev_src_ips IS NOT NULL
  AND  unique_src_ips - prev_src_ips >= 5        -- spike threshold
ORDER  BY new_src_jump DESC;


-- Rolling 30-minute packet total with window functions
-- Good for quick-trend dashboards without separate aggregation tables.
SELECT
    host_ip,
    interval_end,
    SUM(total_packets) OVER (
         PARTITION BY host_ip
         ORDER BY interval_end
         RANGE BETWEEN INTERVAL '30 minutes' PRECEDING AND CURRENT ROW
    ) AS pkts_last_30m
FROM   host_stats
ORDER  BY host_ip, interval_end;


-- Hourly traffic heat-map base table
-- Creates an on-the-fly hourly summary you can pivot in BI tools.
SELECT
    date_trunc('hour', interval_start) AS hour_bucket,
    host_ip,
    SUM(total_packets) AS pkts,
    SUM(total_packets_size) AS bytes
FROM   host_stats
GROUP  BY hour_bucket, host_ip
ORDER  BY hour_bucket DESC, pkts DESC;
