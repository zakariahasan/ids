SELECT src_ip,
       COUNT(*)                                 AS total_alerts,
       COUNT(*) FILTER (WHERE alert_type='Port Scan') AS port_scans,
       COUNT(*) FILTER (WHERE alert_type='DDoS')      AS ddos_hits
FROM   alerts
GROUP  BY src_ip
ORDER  BY total_alerts DESC
LIMIT  5;