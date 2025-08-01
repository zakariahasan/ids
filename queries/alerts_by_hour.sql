SELECT date_trunc('hour', ts)     AS hour_bucket,
       alert_type,
       COUNT(*)                  AS alert_cnt
FROM   alerts
WHERE  ts >= NOW() - INTERVAL '24 hours'
GROUP  BY hour_bucket, alert_type
ORDER  BY hour_bucket, alert_type;