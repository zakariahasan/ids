SELECT ts,
       COUNT(*) FILTER (
         WHERE alert_type = 'DDoS'
       ) OVER (
         ORDER BY ts
         RANGE BETWEEN INTERVAL '10 minutes' PRECEDING AND CURRENT ROW
       ) AS ddos_window
FROM   alerts
ORDER  BY ts;