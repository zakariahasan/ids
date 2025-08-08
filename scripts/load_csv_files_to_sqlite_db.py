"""Load CSV files into the **SQLite** schema defined in *net_analysis.db*.

This is the SQLite counterpart to *load_csv_files_to_tables_postgresql.py*.
It discovers CSV files in ``<BASE_DIR>/data`` and loads them into the
corresponding tables, whose column order is declared in ``TABLE_CONFIGS``.

Database location is taken from ``config.sqlite_config['db_path']`` so you can
change it in **config.py** without touching this script.
"""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
from ids.core import config  # BASE_DIR & sqlite_config live here

# ---------------------------------------------------------------------------
# Paths & logging
# ---------------------------------------------------------------------------

BASE_DIR: Path = config.BASE_DIR
CSV_DIR: Path = BASE_DIR / "data"
LOG_DIR: Path = BASE_DIR / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE: Path = LOG_DIR / "csv_data_loader_sqlite.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.getLogger().addHandler(console)

# ---------------------------------------------------------------------------
# Table → columns mapping (must exactly match CSV headers)
# ---------------------------------------------------------------------------
TABLE_CONFIGS: dict[str, list[str]] = {
    "alerts": [
        "ts",
        "alert_type",
        "src_ip",
        "dst_ip",
        "details",
        "model_name",
    ],
     "users": [
        "id",
        "username",
        "password",
        "role"
    ],
    "host_stats": [
        "interval_start",
        "interval_end",
        "host_ip",
        "total_packets",
        "incoming_packets",
        "outgoing_packets",
        "unique_src_ips",
        "unique_dst_ports",
        "total_packets_size",
    ],
    "packets": [
        "ts",
        "src_ip",
        "src_port",
        "dst_ip",
        "dst_port",
        "protocol",
        "pkt_len",
        "tcp_flags",
        "raw_data",
        "full_url",
    ],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(value: Any) -> Any:  # noqa: D401 – imperative mood
    """Convert pandas NaN/NaT to ``None`` so SQLite stores NULL."""
    if pd.isna(value):
        return None
    return value


def _get_db_path() -> Path:
    """Resolve database path from *config.sqlite_config['db_path']*."""
    raw = Path(config.sqlite_config["db_path"])
    return raw if raw.is_absolute() else BASE_DIR / raw


# ---------------------------------------------------------------------------
# Main routine
# ---------------------------------------------------------------------------

def main() -> None:  # noqa: D401
    logging.info("CSV loader starting – directory: %s", CSV_DIR)

    db_path: Path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        logging.info("Connected to SQLite DB at %s", db_path)
    except sqlite3.Error as exc:
        logging.error("Failed to connect to SQLite: %s", exc)
        return

    cur = conn.cursor()

    for csv_file in CSV_DIR.glob("*.csv"):
        logging.info("Reading %s", csv_file.name)
        try:
            df = pd.read_csv(csv_file)
        except Exception as exc:  # noqa: BLE001 – continue other files
            logging.error("Could not read %s: %s", csv_file.name, exc)
            continue

        header = list(df.columns)

        for table, expected in TABLE_CONFIGS.items():
            if header == expected:
                placeholders = ", ".join(["?"] * len(expected))
                columns = ", ".join(expected)
                sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders});"

                row_count = 0
                try:
                    for _, row in df.iterrows():
                        cur.execute(sql, tuple(_clean(row[col]) for col in expected))
                        row_count += 1
                    conn.commit()
                    logging.info("Inserted %d rows into '%s' from %s", row_count, table, csv_file.name)
                except Exception as exc:
                    logging.error("Insertion failed for %s → %s: %s", csv_file.name, table, exc)
                    conn.rollback()
                break  # header matched, no need to test other tables
        else:
            logging.warning("Header of %s does not match any table; skipping", csv_file.name)

    cur.close()
    conn.close()
    logging.info("CSV loader finished.")


if __name__ == "__main__":
    main()
