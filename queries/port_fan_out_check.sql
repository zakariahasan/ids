-- "Port-fan-out" check – many destination ports hit in last 3 hours
-- Large unique_dst_ports counts can indicate port scanning or very chatty services.
SELECT
    interval_start,
    interval_end,
    host_ip,
    unique_dst_ports
FROM   host_stats
WHERE  unique_dst_ports >= 10          -- threshold; adjust for your baseline
AND interval_end >= NOW() - INTERVAL '2 hour'
ORDER  BY unique_dst_ports DESC;