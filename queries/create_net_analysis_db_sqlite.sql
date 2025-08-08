-- SQLite-compatible schema for the IDS application
-- *******************************************************
-- Table 1: Raw packet logs
CREATE TABLE IF NOT EXISTS packets (
    packet_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts             TEXT,           -- ISO-8601 timestamp
    src_ip         TEXT,
    src_port       INTEGER,
    dst_ip         TEXT,
    dst_port       INTEGER,
    protocol       TEXT,
    pkt_len        INTEGER,
    tcp_flags      TEXT,
    raw_data       BLOB,
	full_url	   TEXT
);

-- Table 2: Alerts for detected attacks
CREATE TABLE IF NOT EXISTS alerts (
    alert_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT,
    alert_type   TEXT,
    src_ip       TEXT,
    dst_ip       TEXT,
    details      TEXT,
    model_name   TEXT
);

-- Table 3: Host statistics per interval
CREATE TABLE IF NOT EXISTS host_stats (
    stats_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    interval_start     TEXT,
    interval_end       TEXT,
    host_ip            TEXT,
    total_packets      INTEGER,
    incoming_packets   INTEGER,
    outgoing_packets   INTEGER,
    unique_src_ips     INTEGER,
    unique_dst_ports   INTEGER,
    total_packets_size INTEGER
);

-- Table 4: Application users
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password      TEXT NOT NULL,
    role          TEXT NOT NULL
);

-- Table 5: Known malicious IP addresses
CREATE TABLE IF NOT EXISTS malicious_ip (
    ip_address TEXT PRIMARY KEY
);
