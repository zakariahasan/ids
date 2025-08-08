"""
Generate synthetic network‑packet records for IDS testing.

Creates a CSV called `synthetic_packets.csv` inside a sibling folder called
`data/` (auto‑created if missing).

**New in 2025‑08‑08**
    • Adds two extra columns:
        1. **raw_data**  – 32‑byte hex dump of the packet payload (e.g. "4A6F...3B").
        2. **full_url** – Random HTTP/HTTPS URL representing the flow if the
          protocol is application‑layer (otherwise left blank).

Run directly:

    python gen_packets_data.py
"""

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

fake = Faker()


HEX_DIGITS = "0123456789ABCDEF"
URL_SCHEMES = ["http", "https"]
PROTOCOLS = ["TCP", "UDP", "TLS", "HTTP", "HTTPS", "RDP"]
TCP_FLAG_OPTS = ["0x0018", "0x0010", "0x0002", "0x0011"]


def _random_hex(len_bytes: int = 32) -> str:
    """Return `len_bytes` * 2‑char hex digits (simulated raw payload)."""
    return "".join(random.choices(HEX_DIGITS, k=len_bytes))


def _random_url() -> str:
    """Return a plausible random HTTP/S URL."""
    scheme = random.choice(URL_SCHEMES)
    domain = fake.domain_name()
    path = fake.uri_path()  # already starts without '/'
    return f"{scheme}://{domain}/{path}"


def generate_synthetic_packets(
    start_dt: datetime,
    end_dt: datetime,
    num_distinct_ips: int,
    total_packets: int,
) -> pd.DataFrame:
    """Build a DataFrame with synthetic packet‑capture data.

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
                 pkt_len, tcp_flags, raw_data, full_url
    """
    ip_pool = [fake.ipv4_public() for _ in range(num_distinct_ips)]

    rows = []
    for _ in range(total_packets):
        ts = fake.date_time_between(start_date=start_dt, end_date=end_dt)
        src_ip = random.choice(ip_pool)
        dst_ip = random.choice([ip for ip in ip_pool if ip != src_ip])

        protocol = random.choice(PROTOCOLS)
        src_port = random.randint(1024, 65535)
        dst_port = random.choice([80, 443, 8080, random.randint(1024, 65535)])
        pkt_len = random.randint(40, 1500)
        tcp_flags = random.choice(TCP_FLAG_OPTS)

        # New fields
        raw_data = _random_hex(32)
        full_url = _random_url() if protocol in {"HTTP", "HTTPS"} else ""

        rows.append(
            {
                "ts": ts,  # datetime; pandas handles serialisation
                "src_ip": src_ip,
                "src_port": src_port,
                "dst_ip": dst_ip,
                "dst_port": dst_port,
                "protocol": protocol,
                "pkt_len": pkt_len,
                "tcp_flags": tcp_flags,
                "raw_data": raw_data,
                "full_url": full_url,
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Script entry‑point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # 24‑hour synthetic capture window
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(hours=24)

    df = generate_synthetic_packets(
        start_dt=start_dt,
        end_dt=end_dt,
        num_distinct_ips=10,
        total_packets=1_000,
    )

    # Dynamic path: <folder‑containing‑this‑file>/../data/synthetic_packets.csv
    here = Path(__file__).resolve()
    data_dir = here.parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    csv_path = data_dir / "synthetic_packets.csv"
    df.to_csv(csv_path, index=False)

    print(f"Saved {len(df)} packets → {csv_path}")
    print(df.head())
