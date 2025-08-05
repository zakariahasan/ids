"""
ids.core.db
~~~~~~~~~~~

PostgreSQL helper with connection pooling + host-stats support.

Usage
-----
>>> from ids.core.db import db
>>> db.insert_packet({...})
>>> db.commit()      # if commit_every > 1
"""

from __future__ import annotations

import contextlib
import datetime as dt
from typing import Any, Mapping

import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool

from . import config

__all__ = ["db", "DatabaseClient"]


class DatabaseClient:
    """Lightweight wrapper around a global `psycopg2` connection-pool."""

    # ------------------------------------------------------------------ #
    # Construction & helpers                                             #
    # ------------------------------------------------------------------ #
    _pool: SimpleConnectionPool | None = None

    def __init__(self, dsn: str, *, commit_every: int = 1) -> None:
        """
        Parameters
        ----------
        dsn
            PostgreSQL DSN string
        commit_every
            Auto-commit every *N* `insert_packet` calls.  Keep **1** to commit
            each write immediately (safest), or raise for better throughput.
        """
        self.dsn = dsn
        self.commit_every = max(1, commit_every)
        self._ops_since_commit = 0

        if DatabaseClient._pool is None:
            DatabaseClient._pool = SimpleConnectionPool(1, 12, dsn=self.dsn)

    # Context-manager so you can do `with db:` if you want an explicit scope
    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.commit()

    # ------------------------------------------------------------------ #
    # Low-level                                                          #
    # ------------------------------------------------------------------ #
    @contextlib.contextmanager
    def _get_conn_cursor(self):
        assert self._pool is not None  # pool is created in __init__
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                yield conn, cur
        finally:
            self._pool.putconn(conn)

    def _execute(self, sql: str, params: Mapping[str, Any] | tuple[Any, ...]):
        with self._get_conn_cursor() as (conn, cur):
            cur.execute(sql, params)

            self._ops_since_commit += 1
            if self._ops_since_commit >= self.commit_every:
                conn.commit()
                self._ops_since_commit = 0

    # ------------------------------------------------------------------ #
    # Inserts                                                            #
    # ------------------------------------------------------------------ #
    def insert_packet(self, pkt: Mapping[str, Any]) -> None:
        self._execute(
            """
            INSERT INTO packets
              (ts, src_ip, src_port, dst_ip, dst_port,
               protocol, pkt_len, tcp_flags)
            VALUES (%(ts)s, %(src_ip)s, %(src_port)s, %(dst_ip)s,
                    %(dst_port)s, %(protocol)s, %(length)s, %(tcp_flags)s)
            """,
            pkt,
        )

    def insert_alert(self, alert: Mapping[str, Any]) -> None:
        self._execute(
            """
            INSERT INTO alerts
              (ts, alert_type, src_ip, dst_ip, details)
            VALUES (%(ts)s, %(alert_type)s, %(src_ip)s, %(dst_ip)s, %(details)s)
            """,
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
            """,
            stats,
        )

    # ------------------------------------------------------------------ #
    # Utilities                                                          #
    # ------------------------------------------------------------------ #
    def execute_sql(self, sql: str) -> None:
        """Run arbitrary SQL (DDL or DML) from a string."""
        try:
            self._execute(sql, {})
        except Exception as exc:  # pragma: no cover
            print(f"[DB] Error executing SQL: {exc}")

    def commit(self) -> None:
        """Force a commit (useful if commit_every > 1)."""
        if self._pool is None:
            return
        with self._get_conn_cursor() as (conn, _cur):
            conn.commit()
        self._ops_since_commit = 0

    def close(self) -> None:
        """Close all pooled connections (call once on program exit)."""
        if self._pool is not None:
            self._pool.closeall()


# --------------------------------------------------------------------------- #
# Global singleton                                                            #
# --------------------------------------------------------------------------- #

db = DatabaseClient(config.DB_DSN, commit_every=1)
