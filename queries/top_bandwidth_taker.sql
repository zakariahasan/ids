-- Top "talkers" by bandwidth in the last 10 minutes
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