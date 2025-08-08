"""Central configuration values.

Populate from environment variables where possible to avoid
committing secrets. Default values below are fine for development.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Packet capture
INTERFACE = os.getenv("IDS_INTERFACE", "Wi-Fi")

# E‑mail alerting
SMTP_SERVER = os.getenv("IDS_SMTP_SERVER", "smtp.gmail.com")
SMTP_USERNAME = os.getenv("IDS_SMTP_USERNAME", "zakaria.tech.sup@gmail.com")
SMTP_PASSWORD = os.getenv("IDS_SMTP_PASSWORD", "nozoaergnisfiyts")
ALERT_RECIPIENT = os.getenv("IDS_ALERT_RECIPIENT", "20029164@students.koi.edu.au")
ALERT_THROTTLE_SEC = int(os.getenv("IDS_ALERT_THROTTLE_SEC", "300"))

# Database
DB_DSN = os.getenv("IDS_DB_DSN", "dbname=net_analysis user=postgres password=postgres321 host=127.0.0.1")
# Configurations (could be loaded from environment variables/YAML)
postgres_config = {
    "type": "postgres",
    "host": "localhost",
    "user": "postgres",
    "password": "postgres321",
    "dbname": "net_analysis"
}

sqlite_config = {
    "type": "sqlite",
    "db_path": str(BASE_DIR / "sqlite_db" / "net_analysis.db"),
}

#Environment
ENVIRONMENT = "prod" #"test"  

# ML
MODEL_DIR = BASE_DIR / "ml_models"
MODEL_DIR.mkdir(exist_ok=True)