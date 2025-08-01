"""
load_csv_files_to_db_tables.py
------------------------------
Scans the gen_data/data directory, loads each CSV that matches one of the
known schemas, and inserts the rows into the corresponding PostgreSQL table.
All paths are built dynamically from config.BASE_DIR, and the database
connection uses the DSN stored in config.DB_DSN.
"""

import logging
from pathlib import Path
import psycopg2
import pandas as pd
from ids.core import config   # ← provides BASE_DIR and DB_DSN

# ---------------------------------------------------------------------------
# Dynamic paths
# ---------------------------------------------------------------------------

BASE_DIR = config.BASE_DIR                        # project root
TARGET_DIRECTORY = BASE_DIR / "data" # CSVs live here
LOG_DIR = BASE_DIR / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "csv_data_loader.log"

# ---------------------------------------------------------------------------
# Table → column mapping
# ---------------------------------------------------------------------------
TABLE_CONFIGS = {
    "alerts": [
        "ts",
        "alert_type",
        "src_ip",
        "dst_ip",
        "details",
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
    ],
}

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)
logging.getLogger("").addHandler(console_handler)

# ---------------------------------------------------------------------------
# Main loader
# ---------------------------------------------------------------------------
def main() -> None:
    logging.info(f"Starting data-load process. Directory: '{TARGET_DIRECTORY}'")

    # --- Connect using DSN ---------------------------------------------------
    try:
        conn = psycopg2.connect(config.DB_DSN)
        logging.info("Successfully connected to PostgreSQL via DSN.")
    except psycopg2.Error as exc:
        logging.error(f"Database connection failed: {exc}")
        return

    cursor = conn.cursor()

    # --- Iterate over *.csv files -------------------------------------------
    for file_path in TARGET_DIRECTORY.glob("*.csv"):
        logging.info(f"Processing file: {file_path}")

        try:
            df = pd.read_csv(file_path)
        except Exception as exc:
            logging.error(f"Failed to read '{file_path}': {exc}")
            continue

        file_columns = list(df.columns)

        # Match file header to a known table schema
        for table_name, expected_columns in TABLE_CONFIGS.items():
            if file_columns == expected_columns:
                logging.info(
                    f"Header matches table '{table_name}'. Loading rows..."
                )

                placeholders = ", ".join(["%s"] * len(expected_columns))
                columns = ", ".join(expected_columns)
                insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders});"

                rows_loaded = 0
                for _, row in df.iterrows():
                    row_data = tuple(row[col] for col in expected_columns)
                    try:
                        cursor.execute(insert_sql, row_data)
                        rows_loaded += 1
                    except Exception as exc:
                        logging.error(f"Error inserting row {row_data}: {exc}")
                        conn.rollback()
                        break  # stop processing this file
                else:
                    conn.commit()
                    logging.info(
                        f"Loaded {rows_loaded} rows from '{file_path.name}' into '{table_name}'."
                    )
                break  # stop checking other table schemas
        else:
            logging.warning(
                f"File '{file_path.name}' header does not match any expected schema. Skipping."
            )

    cursor.close()
    conn.close()
    logging.info("Data-load process complete. Connection closed.")


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
