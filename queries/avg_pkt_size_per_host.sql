--Average packet size per host (all time)
--Useful for spotting hosts that send many small probes vs. large data bursts.
SELECT
    host_ip,
    SUM(total_packets_size)::NUMERIC / NULLIF(SUM(total_packets),0) AS avg_pkt_size_bytes,
    SUM(total_packets)                                              AS total_pkts
FROM   host_stats
GROUP  BY host_ip
ORDER  BY avg_pkt_size_bytes DESC;