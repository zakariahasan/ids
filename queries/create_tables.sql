-- Table 1: Raw packet logs
CREATE TABLE packets (
    packet_id    SERIAL PRIMARY KEY,
    ts    TIMESTAMP,             -- Packet capture timestamp
    src_ip       INET,                  -- Source IP address (IPv4/IPv6)
    src_port     INTEGER,               -- Source port (if applicable, NULL for non-TCP/UDP)
    dst_ip       INET,                  -- Destination IP
    dst_port     INTEGER,               -- Destination port
    protocol     VARCHAR(50),           -- Protocol name (e.g., 'TCP', 'UDP', 'ICMP')
    pkt_len       INTEGER,               -- Packet length in bytes
    tcp_flags    VARCHAR(8),            -- TCP flags (if TCP packet, e.g., 'SYN', 'SYN-ACK')
    raw_data     BYTEA                  -- Raw packet bytes (optional, can store entire packet)
);

-- Table 2: Alerts for detected attacks
CREATE TABLE alerts (
    alert_id     SERIAL PRIMARY KEY,
    ts    TIMESTAMP,            -- Time of detection
    alert_type   VARCHAR(50),          -- Type of alert ('DoS', 'DDoS', 'Port Scan', etc.)
    src_ip       INET,                 -- Source IP involved in attack (if applicable)
    dst_ip       INET,                 -- Target IP involved (if applicable)
    details      TEXT                  -- Description or metadata (e.g., "SYN flood with X SYN packets in Y seconds")
);

-- Table 3: Host statistics per interval (e.g., per minute/hour)
CREATE TABLE host_stats (
    stats_id     SERIAL PRIMARY KEY,
    interval_start TIMESTAMP,         -- Start of time interval (e.g., 2025-03-28 12:00:00)
    interval_end   TIMESTAMP,         -- End of time interval
    host_ip      INET,                -- IP address (could be an internal host or external)
    total_packets INTEGER,            -- Total packets involving this host in interval
    incoming_packets INTEGER,         -- Packets where this host is destination
    outgoing_packets INTEGER,         -- Packets where this host is source
    unique_src_ips  INTEGER,          -- (if host is dest) number of unique source IPs seen
    unique_dst_ports INTEGER,         -- (if host is dest) number of unique destination ports targeted (useful for scan detection)
	total_packets_size INTEGER
);
