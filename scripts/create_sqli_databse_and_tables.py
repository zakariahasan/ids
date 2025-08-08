
"""
Initialize (or refresh) the *net_analysis* SQLite database from a schema file
located in a shared queries/ directory.

Directory layout (relative to this script):
  project_root(ids)/
  ├── queries/
  │   └── create_net_analysis_db_sqlite.sql
  └── srripts/
      └── init_net_analysis_db.py  ← this script

Usage
-----
python init_net_analysis_db.py            # uses the default schema file
python init_net_analysis_db.py --sql custom_schema.sql --db test.db
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Final

# --------------------------------------------------------------------------- #
# Configuration                                                               #
# --------------------------------------------------------------------------- #

# Folder that holds all .sql files used by the project
QUERY_DIR: Final[Path] = Path(__file__).resolve().parent.parent / "queries"

# Default filenames
DEFAULT_SQL_FILE: Final[str] = "create_net_analysis_db_sqlite.sql"
DEFAULT_DB_FILE: Final[str] = Path(__file__).resolve().parent.parent / "sqlite_db" / "net_analysis.db"


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
def init_db(sql_file: str | Path, db_file: str | Path = DEFAULT_DB_FILE) -> None:
    """
    Create (or overwrite) an SQLite database by running the given SQL script.

    Parameters
    ----------
    sql_file : str | Path
        Name of the SQL file *inside* :pydata:`QUERY_DIR` **or** an absolute path.
    db_file : str | Path, default ``net_analysis.db``
        SQLite database file to create or update.
    """
    sql_path = Path(sql_file)
    # If user passed just a bare filename, look for it in QUERY_DIR
    if not sql_path.is_absolute():
        sql_path = QUERY_DIR / sql_path

    if not sql_path.exists():
        raise FileNotFoundError(f"SQL schema not found: {sql_path}")

    db_path = Path(db_file)
    script = sql_path.read_text(encoding="utf-8")

    # Connect and execute script
    with sqlite3.connect(db_path) as conn:
        conn.executescript(script)

    print(f"✔ Database ready: {db_path.resolve()}")


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #
def _parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create an SQLite database from a schema file."
    )
    parser.add_argument(
        "--sql",
        default=DEFAULT_SQL_FILE,
        help=(
            "SQL file to run. If only a filename is provided, it is "
            f"resolved inside {QUERY_DIR}/"
        ),
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB_FILE,
        help="SQLite database file to create/update.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_cli()
    try:
        init_db(sql_file=args.sql, db_file=args.db)
    except Exception as exc:  # broad catch to surface any issue quickly
        print(f"✖ Failed to initialize database: {exc}")
        raise
