-- Top "talkers" by bandwidth in the last 10 minutes
-- Shows which hosts moved the most bytes recently.
-- Top “talkers” by bandwidth in the last 10 minutes (SQLite)
SELECT
    host_ip,
    SUM(total_packets_size) AS bytes_last_10m,
    SUM(total_packets)      AS pkts_last_10m
FROM host_stats
WHERE interval_end >= datetime('now', '-1000 minutes')
GROUP BY host_ip
ORDER BY bytes_last_10m DESC
LIMIT 5;
