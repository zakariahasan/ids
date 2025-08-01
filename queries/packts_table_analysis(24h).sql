--1. Count Total Packets (Last 24 hours):
SELECT COUNT(*) AS total_packets_last_24hrs
FROM packets
WHERE ts >= NOW() - INTERVAL '24 HOURS';
--2. Packets Count by Protocol (Last 24 hours):
SELECT protocol, COUNT(*) AS protocol_count
FROM packets
WHERE ts >= NOW() - INTERVAL '24 HOURS'
GROUP BY protocol
ORDER BY protocol_count DESC;
--3. Average Packet Length by Source IP (Last 24 hours):
SELECT src_ip, AVG(pkt_len) AS avg_packet_length
FROM packets
WHERE ts >= NOW() - INTERVAL '24 HOURS'
GROUP BY src_ip
ORDER BY avg_packet_length DESC;
--4. Most Frequent Source IPs (Last 24 hours):
SELECT src_ip, COUNT(*) AS frequency
FROM packets
WHERE ts >= NOW() - INTERVAL '24 HOURS'
GROUP BY src_ip
ORDER BY frequency DESC
LIMIT 10;
-- 5. Most Frequent Destination IPs (Last 24 hours):
SELECT dst_ip, COUNT(*) AS frequency
FROM packets
WHERE ts >= NOW() - INTERVAL '24 HOURS'
GROUP BY dst_ip
ORDER BY frequency DESC
LIMIT 10;
--6. Port Activity Analysis (Frequent Destination Ports, Last 24 hours):
SELECT dst_port, COUNT(*) AS activity_count
FROM packets
WHERE ts >= NOW() - INTERVAL '24 HOURS'
GROUP BY dst_port
ORDER BY activity_count DESC
LIMIT 10;
--7. TCP Flag Usage Analysis (Last 24 hours):
SELECT tcp_flags, COUNT(*) AS flag_usage
FROM packets
WHERE ts >= NOW() - INTERVAL '24 HOURS'
GROUP BY tcp_flags
ORDER BY flag_usage DESC;
--8. Hourly Traffic Analysis (Packets Per Hour in Last 24 hours):
SELECT DATE_TRUNC('hour', ts::timestamp) AS hour,
       COUNT(*) AS packets_per_hour
FROM packets
WHERE ts >= NOW() - INTERVAL '24 HOURS'
GROUP BY hour
ORDER BY hour;
--9. Source-Destination IP Pairs Analysis (Last 24 hours):
SELECT src_ip, dst_ip, COUNT(*) AS pair_count
FROM packets
WHERE ts >= NOW() - INTERVAL '24 HOURS'
GROUP BY src_ip, dst_ip
ORDER BY pair_count DESC
LIMIT 10;
--10. Peak Packet Lengths (Top 10 longest packets, Last 24 hours):
SELECT *
FROM packets
WHERE ts >= NOW() - INTERVAL '24 HOURS'
ORDER BY pkt_len DESC
LIMIT 10;
