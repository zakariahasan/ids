"""Inspect an SQLite database: list tables, columns & sample rows.

The script discovers the database location from ``config.sqlite_config['db_path']``
(just like the CSV loader).  It prints, to *stdout*, all user‑defined tables,
column metadata and the first *N* rows (default **5**) per table.

Usage (from project root)::

    python -m ids.scripts.inspect_sqlite_schema            # default 5 rows
    python -m ids.scripts.inspect_sqlite_schema --rows 10   # custom sample size
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Final

from ids.core import config

# ---------------------------------------------------------------------------
# Helpers / configuration
# ---------------------------------------------------------------------------

BASE_DIR: Final[Path] = config.BASE_DIR


def _get_db_path() -> Path:
    """Resolve DB path from *config.sqlite_config['db_path']*."""
    raw = Path(config.sqlite_config["db_path"])
    return raw if raw.is_absolute() else BASE_DIR / raw


def _list_tables(conn: sqlite3.Connection) -> list[str]:
    """Return user tables (exclude internal *sqlite_%*)."""
    sql = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
    """
    return [row[0] for row in conn.execute(sql)]


def _describe_table(conn: sqlite3.Connection, table: str) -> None:
    """Print column info and sample rows for *table*."""
    print(f"\n=== Table: {table} ===")

    # Column metadata ---------------------------------------------------
    info = conn.execute(f"PRAGMA table_info({table});").fetchall()
    if not info:
        print("(No columns found)")
        return

    # Print columns in a compact table
    print("Columns:")
    for cid, name, col_type, notnull, dflt, pk in info:
        nn = "NOT NULL" if notnull else "NULL"
        pk_flag = "PK" if pk else "  "
        default = f"DEFAULT {dflt}" if dflt is not None else ""
        print(f"  • {name:<20} {col_type:<12} {nn:<8} {pk_flag} {default}")

    # Sample rows -------------------------------------------------------
    print("\nSample rows:")
    cols = ", ".join([i[1] for i in info])
    sample_sql = f"SELECT {cols} FROM {table} LIMIT {args.rows};"
    rows = conn.execute(sample_sql).fetchall()
    if rows:
        # Pretty‑print rows
        for row in rows:
            print("  ", dict(row))
    else:
        print("  (no data)")


# ---------------------------------------------------------------------------
# CLI & main
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect SQLite schema & data")
    parser.add_argument("--rows", type=int, default=5, help="Sample rows per table (default 5)")
    return parser.parse_args()


def main() -> None:  # noqa: D401
    global args  # access inside _describe_table
    args = _parse_args()

    db_path = _get_db_path()
    if not db_path.exists():
        raise SystemExit(f"Database file not found: {db_path}")

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        tables = _list_tables(conn)
        if not tables:
            print("No user tables found in database.")
            return
        print(f"Database: {db_path}  |  Tables: {len(tables)}")
        for tbl in tables:
            _describe_table(conn, tbl)


if __name__ == "__main__":
    main()
