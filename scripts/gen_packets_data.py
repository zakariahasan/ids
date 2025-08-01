"""
Generate synthetic network-packet records for IDS testing.

Creates a CSV called `synthetic_packets.csv` inside a sibling folder called
`data/` (auto-created if missing).

Run directly:

    python gen_packets_data.py
"""

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

fake = Faker()


def generate_synthetic_packets(
    start_dt: datetime,
    end_dt: datetime,
    num_distinct_ips: int,
    total_packets: int,
) -> pd.DataFrame:
    """
    Build a DataFrame with synthetic packet-capture data.

    Parameters
    ----------
    start_dt, end_dt : datetime
        Time window for the generated packets.
    num_distinct_ips : int
        Size of the IP address pool (both source and destination).
    total_packets : int
        Number of rows to generate.

    Returns
    -------
    pandas.DataFrame
        Columns: ts, src_ip, src_port, dst_ip, dst_port, protocol,
                 pkt_len, tcp_flags
    """
    protocols = ["TCP", "UDP", "TLS", "HTTP", "HTTPS", "RDP"]
    tcp_flag_opts = ["0x0018", "0x0010", "0x0002", "0x0011"]
    ip_pool = [fake.ipv4_public() for _ in range(num_distinct_ips)]

    rows = []
    for _ in range(total_packets):
        ts = fake.date_time_between(start_date=start_dt, end_date=end_dt)
        src_ip = random.choice(ip_pool)
        dst_ip = random.choice([ip for ip in ip_pool if ip != src_ip])

        rows.append(
            {
                "ts": ts,  # keep as datetime; Pandas serialises cleanly
                "src_ip": src_ip,
                "src_port": random.randint(1024, 65535),
                "dst_ip": dst_ip,
                "dst_port": random.choice([80, 443, 8080, random.randint(1024, 65535)]),
                "protocol": random.choice(protocols),
                "pkt_len": random.randint(40, 1500),
                "tcp_flags": random.choice(tcp_flag_opts),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# Script entry-point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    # 24-hour synthetic capture window
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(hours=24)

    df = generate_synthetic_packets(
        start_dt=start_dt,
        end_dt=end_dt,
        num_distinct_ips=10,
        total_packets=1_000,
    )

    # Dynamic path: <folder-containing-this-file>/data/synthetic_packets.csv
    here = Path(__file__).resolve()
    data_dir = here.parent.parent / "data"        # step sideways, not hard-coded
    data_dir.mkdir(parents=True, exist_ok=True)

    csv_path = data_dir / "synthetic_packets.csv"
    df.to_csv(csv_path, index=False)

    print(f"Saved {len(df)} packets → {csv_path}")
    print(df.head())
