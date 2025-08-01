# Print Logo
"""
  ______     _              _         _    _                        
 |___  /    | |            (_)       | |  | |                      
    / / __ _| | ____ _ _ __ _  __ _  | |__| | __ _ ___  __ _ _ __  
   / / / _` | |/ / _` | '__| |/ _` | |  __  |/ _` / __|/ _` | '_ \ 
  / /_| (_| |   < (_| | |  | | (_| | | |  | | (_| \__ \ (_| | | | |
 /_____\__,_|_|\_\__,_|_|  |_|\__,_| |_|  |_|\__,_|___/\__,_|_| |_|
   
"""
#print("\n****************************************************************")
#print("\n* Copyright of Zakaria Hasan, 20225                            *")
#print("\n****************************************************************")

"""
generate_dummy_data.py
----------------------
Create a baseline CSV of synthetic “normal” traffic metrics.

The file is saved as:
    <folder-containing-this-script> / data / normal_traffic_baseline.csv
"""

from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

# --------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------

NUM_SAMPLES = 1_000   # rows to generate
RNG_SEED     = 42     # reproducibility

np.random.seed(RNG_SEED)

# --------------------------------------------------------------------
# Data generation
# --------------------------------------------------------------------

data = {
    "src_ip": [f"192.168.0.{i % 255}" for i in range(NUM_SAMPLES)],
    "packet_rate":       np.random.normal(loc=100, scale=20, size=NUM_SAMPLES),   # packets/sec
    "unique_port_count": np.random.normal(loc=10,  scale=3,  size=NUM_SAMPLES),   # distinct ports
    "avg_pkt_size":      np.random.normal(loc=500, scale=50, size=NUM_SAMPLES),   # bytes
    "generated_at":      [datetime.now()] * NUM_SAMPLES,                          # provenance
}

df = pd.DataFrame(data)

# Clamp to sensible minimums
df["packet_rate"]       = df["packet_rate"].clip(lower=0)
df["unique_port_count"] = df["unique_port_count"].clip(lower=1)
df["avg_pkt_size"]      = df["avg_pkt_size"].clip(lower=64)  # min Ethernet frame size

# --------------------------------------------------------------------
# Save to CSV (dynamic path)
# --------------------------------------------------------------------

here = Path(__file__).resolve()
data_dir = here.parent.parent / "data"          # sibling folder
data_dir.mkdir(parents=True, exist_ok=True)

csv_path = data_dir / "normal_traffic_baseline.csv"
df.to_csv(csv_path, index=False)

print(f"Saved {len(df)} rows → {csv_path}")
print(df.head())
