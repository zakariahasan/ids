/* Counts per alert type for the past 1 h, 12 h, and 24 h */
SELECT
    alert_type,src_ip,
    COUNT(*) FILTER (WHERE ts >= NOW() - INTERVAL '1 hour')  AS last_1h,
    COUNT(*) FILTER (WHERE ts >= NOW() - INTERVAL '1000 hour') AS last_12h,
    COUNT(*) FILTER (WHERE ts >= NOW() - INTERVAL '24 hour') AS last_24h
FROM alerts
WHERE ts >= NOW() - INTERVAL '1000 hour'    -- only scan the last 24 h
GROUP BY alert_type , src_ip
ORDER BY alert_type,  src_ip;

-- Counts per alert-type, bucketed by hour (last 24 h)
-- Quick view of hourly activity—great for heat-maps or spark-line charts.
SELECT date_trunc('hour', ts)     AS hour_bucket,
       alert_type,
       COUNT(*)                   AS alert_cnt
FROM   alerts
WHERE  ts >= NOW() - INTERVAL '24 hours'
GROUP  BY hour_bucket, alert_type
ORDER  BY hour_bucket DESC, alert_cnt DESC;

-- Top 5 “noisiest” source IPs overall
-- Shows which attackers trigger your IDS most often and what kind of trouble they cause.
SELECT src_ip,
       COUNT(*) AS total_alerts,
       COUNT(*) FILTER (WHERE alert_type = 'Port Scan') AS port_scans,
       COUNT(*) FILTER (WHERE alert_type = 'DDoS')      AS ddos_hits
FROM   alerts
GROUP  BY src_ip
ORDER  BY total_alerts DESC
LIMIT  5;

--Most-attacked destination IPs, broken down by category
-- Pinpoints the internal host(s) absorbing the brunt of attacks.
SELECT dst_ip,
       alert_type,
       COUNT(*) AS hits
FROM   alerts
GROUP  BY dst_ip, alert_type
ORDER  BY hits DESC, dst_ip;


-- Average time-gap between consecutive alerts (overall & per type)
-- Helps answer: “How frantic is the alert stream?”
WITH gaps AS (
  SELECT alert_type,
         ts,
         ts - LAG(ts) OVER (PARTITION BY alert_type ORDER BY ts) AS gap
  FROM   alerts
)
SELECT alert_type,
       ROUND(AVG(EXTRACT(EPOCH FROM gap))::numeric, 1) AS avg_gap_seconds
FROM   gaps
WHERE  gap IS NOT NULL
GROUP  BY alert_type
UNION ALL
SELECT 'ALL TYPES',
       ROUND(AVG(EXTRACT(EPOCH FROM gap))::numeric, 1)
FROM (
  SELECT ts,
         ts - LAG(ts) OVER (ORDER BY ts) AS gap
  FROM   alerts
) AS g
WHERE  gap IS NOT NULL;


-- Rolling 10-minute DDoS count (window function)
-- Drop into a time-series chart and you’ll spot DDoS flurries instantly.
SELECT ts,
       COUNT(*) FILTER (
         WHERE alert_type = 'DDoS'
       ) OVER (
         ORDER BY ts
         RANGE BETWEEN INTERVAL '10 minutes' PRECEDING AND CURRENT ROW
       ) AS ddos_last_10m
FROM   alerts
ORDER  BY ts;

-- Minute-by-minute alert volume (all types)
-- A finer-grained view than the hourly bucket.
SELECT date_trunc('minute', ts) AS minute_bucket,
       COUNT(*)                AS alerts_in_min
FROM   alerts
GROUP  BY minute_bucket
ORDER  BY minute_bucket;

-- Extract packet counts from DDoS details and rank the heaviest floods
-- Tells you which DDoS entries moved the biggest packet loads.
-- Assumes '... #### packets ->' in details
SELECT alert_id,
       src_ip,
       dst_ip,
       REGEXP_REPLACE(details, '.*?([0-9]+) packets.*', '\1')::INT AS packet_count,
       ts
FROM   alerts
WHERE  alert_type = 'DDoS'
ORDER  BY packet_count DESC
LIMIT  10;

--Detect “burst” Port-scan episodes (≥ 3 scans from same attacker in 30 s)
-- Highlights concentrated scans instead of isolated probes.

WITH scans AS (
  SELECT alert_id, ts, src_ip,
         ts - LAG(ts) OVER (PARTITION BY src_ip ORDER BY ts) AS gap
  FROM   alerts
  WHERE  alert_type = 'Port Scan'
),
clusters AS (
  SELECT *,
         SUM(CASE WHEN gap IS NULL OR gap > INTERVAL '30 seconds' THEN 1 ELSE 0 END)
         OVER (PARTITION BY src_ip ORDER BY ts) AS burst_id
  FROM   scans
)
SELECT src_ip,
       MIN(ts) AS burst_start,
       MAX(ts) AS burst_end,
       COUNT(*) AS scans_in_burst
FROM   clusters
GROUP  BY src_ip, burst_id
HAVING COUNT(*) >= 3
ORDER  BY scans_in_burst DESC;


-- Quiet periods – gaps ≥ 10 min with zero alerts
-- Useful to confirm the IDS is running; long silences might also mark maintenance windows.
WITH ordered AS (
  SELECT ts,
         LAG(ts)  OVER (ORDER BY ts) AS prev_ts
  FROM   alerts
),
gaps AS (
  SELECT prev_ts,
         ts              AS next_ts,
         ts - prev_ts    AS silence
  FROM   ordered
  WHERE  prev_ts IS NOT NULL
)
SELECT prev_ts  AS gap_start,
       next_ts  AS gap_end,
       silence
FROM   gaps
WHERE  silence >= INTERVAL '10 minutes'
ORDER  BY silence DESC;


-- Alerts per attacker and victim (top pairs)
-- Shows repeat offender–target pairs and what they tried.
SELECT src_ip,
       dst_ip,
       COUNT(*) AS pair_alerts,
       ARRAY_AGG(DISTINCT alert_type) AS types_seen
FROM   alerts
GROUP  BY src_ip, dst_ip
ORDER  BY pair_alerts DESC
LIMIT  8;


-- Quick DDL / import snippet (if you haven’t loaded the data)
-- These queries should give you a well-rounded view of attack trends, high-risk hosts, burst behaviour, 
-- and quiet stretches—ideal starting points for dashboards or ad-hoc investigations.
CREATE TABLE alerts (
    alert_id   SERIAL PRIMARY KEY,
    ts         TIMESTAMPTZ,
    alert_type TEXT,
    src_ip     INET,
    dst_ip     INET,
    details    TEXT
);

