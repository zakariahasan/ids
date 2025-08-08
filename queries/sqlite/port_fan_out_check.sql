-- "Port-fan-out" check – many destination ports hit in last 3 hours
-- Large unique_dst_ports counts can indicate port scanning or very chatty services.
-- “Port fan-out” check (SQLite)
SELECT
    interval_start,
    interval_end,
    host_ip,
    unique_dst_ports
FROM host_stats
WHERE unique_dst_ports >= 10
  AND interval_end >= datetime('now', '-12 hours')
ORDER BY unique_dst_ports DESC;
