import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta
from pathlib import Path

fake = Faker()


def generate_host_stats(
    start_dt: datetime,
    end_dt: datetime,
    interval_minutes: int,
    num_distinct_hosts: int,
    total_records: int,
) -> pd.DataFrame:
    """
    Generate synthetic per-host traffic statistics between start_dt and end_dt.

    Parameters
    ----------
    start_dt : datetime
        Beginning of the time range.
    end_dt : datetime
        End of the time range.
    interval_minutes : int
        Length of each statistics interval.
    num_distinct_hosts : int
        Number of unique host IPs to simulate.
    total_records : int
        Maximum total number of rows to return.

    Returns
    -------
    pandas.DataFrame
        Synthetic host statistics with one row per host per interval.
    """
    host_ips = [fake.ipv4_private() for _ in range(num_distinct_hosts)]

    intervals = []
    current_time = start_dt

    while current_time < end_dt and len(intervals) < total_records:
        interval_start = current_time
        interval_end = interval_start + timedelta(minutes=interval_minutes)
        current_time = interval_end

        for host_ip in host_ips:
            total_packets = random.randint(1, 500)
            incoming_packets = random.randint(0, total_packets)
            outgoing_packets = total_packets - incoming_packets
            unique_src_ips = random.randint(1, 20)
            unique_dst_ports = random.randint(0, 20)
            total_packets_size = random.randint(100, 15_000)

            intervals.append(
                {
                    "interval_start": interval_start,  # keep as datetime
                    "interval_end": interval_end,
                    "host_ip": host_ip,
                    "total_packets": total_packets,
                    "incoming_packets": incoming_packets,
                    "outgoing_packets": outgoing_packets,
                    "unique_src_ips": unique_src_ips,
                    "unique_dst_ports": unique_dst_ports,
                    "total_packets_size": total_packets_size,
                }
            )

            if len(intervals) >= total_records:
                break

    return pd.DataFrame(intervals)


# --------------------------- Example usage ---------------------------

end_dt = datetime.now()
start_dt = end_dt - timedelta(hours=24)

synthetic_host_stats_df = generate_host_stats(
    start_dt=start_dt,
    end_dt=end_dt,
    interval_minutes=30,
    num_distinct_hosts=5,
    total_records=1_000,
)

# --------------------------- Save to CSV -----------------------------

here = Path(__file__).resolve()
proj_root = here.parent.parent  # step up one level; adjust if needed

target_dir = proj_root / "data"
target_dir.mkdir(parents=True, exist_ok=True)

csv_path = target_dir / "synthetic_host_stats.csv"
synthetic_host_stats_df.to_csv(csv_path, index=False)

print(f"Saved {len(synthetic_host_stats_df)} rows to {csv_path}")
print(synthetic_host_stats_df.head())
