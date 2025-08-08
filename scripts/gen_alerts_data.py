import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta
from pathlib import Path

fake = Faker()

def generate_synthetic_alerts(
    start_dt: datetime,
    end_dt: datetime,
    num_distinct_src_ips: int,
    total_alerts: int,
) -> pd.DataFrame:
    """
    Create synthetic IDS alert data between start_dt and end_dt.

    Parameters
    ----------
    start_dt, end_dt : datetime
        Time range for generated alerts.
    num_distinct_src_ips : int
        Number of unique attacker source IP addresses.
    total_alerts : int
        Total rows to generate.

    Returns
    -------
    pandas.DataFrame
        Columns: ts, alert_type, src_ip, dst_ip, details, model_name
    """
    alert_types = ["Port Scan", "DDoS", "DoS", "SYN Flood"]
    model_names = ["Random Forest", "Decision Tree", "Linear SVM"]  # ← new

    src_ips = [fake.ipv4_public() for _ in range(num_distinct_src_ips)]
    dst_ip = "192.168.1.109"  # fixed destination IP for simplicity

    rows = []

    for _ in range(total_alerts):
        ts = fake.date_time_between(start_date=start_dt, end_date=end_dt)
        alert_type = random.choice(alert_types)
        src_ip = random.choice(src_ips)
        model_name = random.choice(model_names)  # ← pick one model per row

        if alert_type == "Port Scan":
            details = (
                f"{src_ip} scanned {random.randint(50, 150)} ports "
                f"in {random.randint(1, 10)} s"
            )
        elif alert_type == "DDoS":
            details = (
                f"{random.randint(20, 100)} sources, "
                f"{random.randint(1_000, 5_000)} packets → {dst_ip} "
                f"in {random.randint(5, 20)} s"
            )
        elif alert_type == "DoS":
            details = (
                f"{src_ip} sent {random.randint(500, 2_000)} packets "
                f"to {dst_ip} in {random.randint(5, 20)} s"
            )
        else:  # SYN Flood
            details = (
                f"SYN flood from {src_ip}, "
                f"{random.randint(500, 1_500)} SYN packets "
                f"in {random.randint(1, 10)} s"
            )

        rows.append(
            {
                "ts": ts,  # keep as datetime
                "alert_type": alert_type,
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "details": details,
                "model_name": model_name,  # ← new column
            }
        )

    return pd.DataFrame(rows)


# ------------------------ Example usage ------------------------

if __name__ == "__main__":
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(hours=48)

    synthetic_alerts_df = generate_synthetic_alerts(
        start_dt=start_dt,
        end_dt=end_dt,
        num_distinct_src_ips=10,
        total_alerts=1_000,
    )

    # --------------------------- Save ------------------------------

    here = Path(__file__).resolve()
    proj_root = here.parent.parent  # step up two levels

    data_dir = proj_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    csv_path = data_dir / "synthetic_alerts.csv"
    synthetic_alerts_df.to_csv(csv_path, index=False)

    print(f"Saved {len(synthetic_alerts_df)} alerts → {csv_path}")
    print(synthetic_alerts_df.head())
