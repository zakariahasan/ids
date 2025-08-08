"""
Database abstraction layer with factory + convenience service.

Provides:
* :class:`Database` – abstract interface.
* :class:`PostgresDB` / :class:`SQLiteDB` – concrete back‑ends.
* :class:`DatabaseFactory` – pick back‑end from config dict.
* :class:`DatabaseService` – wrapper that auto‑manages connections.
"""
from __future__ import annotations

import re
import sqlite3  # built‑in – always available
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Mapping
import os

from pathlib import Path
import os, sqlite3, importlib.resources as pkg
try:
    import psycopg2  # noqa: WPS433 (external dependency)
    from psycopg2.extras import RealDictCursor
except ModuleNotFoundError:  # pragma: no cover – library not installed
    psycopg2 = None  # type: ignore[assignment]
    RealDictCursor = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------


class Database(ABC):
    """Abstract database interface: connect → query → close."""

    @abstractmethod
    def connect(self) -> None:  # noqa: D401
        """Open the underlying connection (idempotent)."""

    @abstractmethod
    def query(self, sql: str) -> List[Dict[str, Any]]:  # noqa: D401
        """Execute *sql* and return the full result set as a list of dicts."""

    @abstractmethod
    def close(self) -> None:  # noqa: D401
        """Close the connection if it is open."""


# ---------------------------------------------------------------------------
# PostgreSQL implementation (optional dependency)
# ---------------------------------------------------------------------------


class PostgresDB(Database):
    """PostgreSQL backend built on top of *psycopg2* (with autocommit on)."""

    def __init__(self, host: str, user: str, password: str, dbname: str):
        self._cred = dict(host=host, user=user, password=password, dbname=dbname)
        self._conn: "psycopg2.connection | None" = None

    # Database -----------------------------------------------------------------

    def connect(self) -> None:  # noqa: D401
        """Open a new connection if none is active (autocommit enabled)."""
        if self._conn is None:
            if psycopg2 is None:  # pragma: no cover – dependency missing
                raise RuntimeError("psycopg2 is required for PostgresDB")
            self._conn = psycopg2.connect(cursor_factory=RealDictCursor, **self._cred)
            self._conn.autocommit = True  # ensure DDL/DML is committed automatically

    def query(self, sql: str) -> List[Dict[str, Any]]:  # noqa: D401
        """Run *sql* and return rows as list of dictionaries."""
        if self._conn is None:
            raise RuntimeError("Connection is not open – call connect() first")
        with self._conn.cursor() as cur:
            cur.execute(sql)
            return list(cur.fetchall())

    def close(self) -> None:  # noqa: D401
        """Close connection and reset handle."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None


# ---------------------------------------------------------------------------
# SQLite implementation (always available)
# ---------------------------------------------------------------------------


class SQLiteDB(Database):
    """SQLite backend using :pymod:`sqlite3` with ``row_factory`` for dict rows."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        if self._conn is None:
            os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
            # NEW ─ detect first run
            first_run = not Path(self._db_path).exists()

            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row

            if first_run:
                base_dir = Path(__file__).resolve().parent.parent  # → ids/
                schema_file = base_dir / "queries" / "create_net_analysis_db_sqlite.sql"
                schema = schema_file.read_text(encoding="utf-8")
                self._conn.executescript(schema)

    def query(self, sql: str) -> List[Dict[str, Any]]:  # noqa: D401
        """Execute *sql* and return list of row‑dicts."""
        if self._conn is None:
            raise RuntimeError("Connection is not open – call connect() first")
        cur = self._conn.cursor()
        cur.execute(sql)
        return [dict(row) for row in cur.fetchall()]

    def close(self) -> None:  # noqa: D401
        """Close database file if open."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class DatabaseFactory:
    """Return the correct backend instance from a config mapping."""

    @staticmethod
    def create_database(cfg: Dict[str, Any]) -> Database:  # noqa: D401
        """Instantiate :class:`Database` based on ``cfg['type']`` key."""
        db_type = cfg.get("type")
        if db_type == "postgres":
            return PostgresDB(
                host=cfg["host"],
                user=cfg["user"],
                password=cfg["password"],
                dbname=cfg["dbname"],
            )
        if db_type == "sqlite":
            return SQLiteDB(db_path=cfg["db_path"])
        raise ValueError(f"Unsupported database type: {db_type!r}")


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------


class DatabaseService:
    """Simplify usage: auto‑connect/close on every call."""

    def __init__(self, db: Database):
        self._db = db

    # ----------------------- low‑level helpers ------------------------------- #
    def _execute(self, sql: str, params: Mapping[str, Any]) -> None:
        """Execute *sql* (INSERT/UPDATE/etc.) with *params* on the wrapped DB.

        Adapts parameter placeholders automatically for SQLite (":name") and
        PostgreSQL ("%(name)s"). Autocommit is enabled for both back‑ends.
        """
        self._db.connect()
        try:
            if isinstance(self._db, PostgresDB):
                conn = self._db._conn  # type: ignore[attr-defined]
                assert conn is not None
                with conn.cursor() as cur:
                    cur.execute(sql, params)
            elif isinstance(self._db, SQLiteDB):
                conn = self._db._conn
                assert conn is not None
                # Convert psycopg2-style %(name)s placeholders → :name
                adapted_sql = re.sub(r"%\((\w+)\)s", r":\1", sql)
                conn.execute(adapted_sql, params)
                conn.commit()  # ensure data is persisted in SQLit
            else:  # pragma: no cover – future back‑ends
                raise RuntimeError("Unsupported database backend")
        finally:
            self._db.close()

    # --------------------------- query helpers ------------------------------ #
    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """Run *SELECT* and return rows."""
        self._db.connect()
        try:
            return self._db.query(sql)
        finally:
            self._db.close()

    def execute_non_query(self, sql: str) -> None:
        """Run DDL/DML – no result set returned."""
        self.execute_query(sql)  # autocommit enabled in both back‑ends

    # ------------------------------------------------------------------ #
    # Inserts                                                            #
    # ------------------------------------------------------------------ #
    def insert_packet(self, pkt: Mapping[str, Any]) -> None:
        self._execute(
            """
            INSERT INTO packets
              (ts, src_ip, src_port, dst_ip, dst_port,
               protocol, pkt_len, tcp_flags, full_url)
            VALUES (%(ts)s, %(src_ip)s, %(src_port)s, %(dst_ip)s,
                    %(dst_port)s, %(protocol)s, %(length)s, %(tcp_flags)s, %(full_url)s)
            """.strip(),
            pkt,
        )

    def insert_alert(self, alert: Mapping[str, Any]) -> None:
        self._execute(
            """
            INSERT INTO alerts
              (ts, alert_type, src_ip, dst_ip, details, model_name)
            VALUES (%(ts)s, %(alert_type)s, %(src_ip)s, %(dst_ip)s,
                    %(details)s, %(model_name)s)
            """.strip(),
            alert,
    )

    def insert_host_stats(self, stats: Mapping[str, Any]) -> None:
        self._execute(
            """
            INSERT INTO host_stats
              (interval_start, interval_end, host_ip,
               total_packets, incoming_packets, outgoing_packets,
               unique_src_ips, unique_dst_ports, total_packets_size)
            VALUES (%(interval_start)s, %(interval_end)s, %(host_ip)s,
                    %(total_packets)s, %(incoming_packets)s,
                    %(outgoing_packets)s, %(unique_src_ips)s,
                    %(unique_dst_ports)s, %(total_packets_size)s)
            """.strip(),
            stats,
        )


__all__ = [
    "Database",
    "PostgresDB",
    "SQLiteDB",
    "DatabaseFactory",
    "DatabaseService",
]
