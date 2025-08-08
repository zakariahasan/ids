from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import codecs
from flask import Blueprint, jsonify, render_template
from sqlalchemy import text

from ids.web.extensions import db

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

#   ids/
#     ├─ queries/
#     │   ├─ host_count.sql              ← Postgres default
#     │   ├─ sqlite/host_count.sql       ← (optional) SQLite-specific override
#     │   └─ …
QUERY_DIR = Path(__file__).resolve().parent.parent.parent / "queries"


# --------------------------------------------------------------------------- #
# Helper: load & adapt SQL                                                    #
# --------------------------------------------------------------------------- #
POSTGRES_CAST_RE = re.compile(r"::\s*\w+")
# 2025-08-08 05:28:01  or  2025-08-08 05:28:01.417
DT_RE = re.compile(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d(?:\.\d+)?")

def _adapt_sql_for_sqlite(sql: str) -> str:
    """Best-effort convert a Postgres query into SQLite."""
    # – remove '::type' casts -------------------------------------------------
    sql = POSTGRES_CAST_RE.sub("", sql)

    # – date_trunc('hour', ts) ➜ strftime('%Y-%m-%d %H:00:00', ts)
    sql = re.sub(
        r"date_trunc\s*\(\s*'(\w+)'\s*,\s*([^)]+)\)",
        lambda m: (
            f"strftime('%Y-%m-%d %H:00:00', {m.group(2)})"
            if m.group(1) == "hour"
            else f"strftime('%Y-%m-%d', {m.group(2)})"
        ),
        sql,
        flags=re.IGNORECASE,
    )

    return sql


def _load_sql(file_name: str) -> str:
    """Return the SQL string appropriate for the current DB backend."""
    dialect = db.get_engine().dialect.name  # 'postgresql', 'sqlite', …
    if dialect == "sqlite":
        alt = QUERY_DIR / "sqlite" / file_name
        if alt.exists():
            return alt.read_text(encoding="utf-8", errors="replace")

        # Fallback: try to adapt the Postgres version automatically
        return _adapt_sql_for_sqlite((QUERY_DIR / file_name).read_text())

    # Postgres / others – use canonical query as-is
    return (QUERY_DIR / file_name).read_text()


# changed today

def run_sql(filename: str):
    sql  = _load_sql(filename)          # keeps the SQLite/Postgres switch
    rows = db.session.execute(text(sql)).mappings().all()
    # materialise as real dicts so routes can tweak them safely
    return [_coerce_sqlite_types(dict(r)) for r in rows]

# --------------------------------------------------------------------------- #
# Helper: normalise SQLite return types                                       #
# --------------------------------------------------------------------------- #
def _coerce_sqlite_types(row: Dict[str, Any]) -> Dict[str, Any]:
    """Convert SQLite strings → datetime objects to match Postgres behaviour."""
    for k, v in row.items():
        if isinstance(v, str):
            try:
                row[k] = datetime.fromisoformat(v.replace(" ", "T"))
            except ValueError:
                # Py 3.10 needs .fromisoformat("YYYY-MM-DD HH:MM:SS.SSS")
                #row[k] = datetime.strptime(v, "%Y-%m-%d %H:%M:%S.%f")
                pass 
    return row


# --------------------------------------------------------------------------- #
# Routes                                                                      #
# --------------------------------------------------------------------------- #
@bp.route("/")
def view():
    return render_template("dashboard.html")


@bp.route("/top_hosts")
def api_top_hosts():
    return jsonify(run_sql("host_count.sql"))


@bp.route("/alerts_by_hour")
def alerts_by_hour():
    rows = run_sql("alerts_by_hour.sql")
    buckets: Dict[str, Dict[str, int]] = {}
    for row in rows:
        hour = (row["hour_bucket"].strftime("%Y-%m-%d %H:%M")
        if hasattr(row["hour_bucket"], "strftime")
        else datetime.fromisoformat(row["hour_bucket"]).strftime("%Y-%m-%d %H:%M"))
        buckets.setdefault(hour, {})[row["alert_type"]] = row["alert_cnt"]
    return jsonify(buckets)


@bp.route("/top_sources")
def top_sources():
    return jsonify(run_sql("top_sources.sql"))


@bp.route("/ddos_last_10m")
def ddos_last_10m():
    rows = run_sql("ddos_last_10m.sql")
    return jsonify([
        {                       # SQLite returns 'YYYY-MM-DD HH:MM:SS'
            "timestamp": r["ts"],          # <- keep as-is
            "count": int(r["ddos_window"])
        }
        for r in rows
    ])


@bp.route("/scan_bursts")
def scan_bursts():
    rows = run_sql("scan_bursts.sql")        # already a list of dicts
    payload = [
        {
            "src_ip":          r["src_ip"],
            "burst_start":     r["burst_start"],   # ISO-8601 string from SQLite
            "burst_end":       r["burst_end"],
            "scans_in_burst":  int(r["scans_in_burst"]),
        }
        for r in rows
    ]
    return jsonify(payload)


@bp.route("/top_bandwidth")
def top_bandwidth():
    rows = run_sql("top_bandwidth_taker.sql")
    for r in rows:  # ensure JSON-friendly ints
        r["bytes_last_10m"] = int(r["bytes_last_10m"])
        r["pkts_last_10m"] = int(r["pkts_last_10m"])
    return jsonify(rows)


@bp.route("/avg_pkt_size")
def avg_pkt_size():
    rows = run_sql("avg_pkt_size_per_host.sql")
    for r in rows:
        r["avg_pkt_size_bytes"] = float(r["avg_pkt_size_bytes"])
        r["total_pkts"] = int(r["total_pkts"])
    return jsonify(rows)


@bp.route("/heavy_outgoing")
def heavy_outgoing():
    rows = run_sql("host_with_heavy_outgoing.sql")
    for r in rows:
        r["in_pkts"] = int(r["in_pkts"])
        r["out_pkts"] = int(r["out_pkts"])
        r["out_in_ratio"] = float(r["out_in_ratio"])
    return jsonify(rows)


@bp.route("/port_fanout")
def port_fanout():
    rows = run_sql("port_fan_out_check.sql")
    agg: Dict[str, int] = {}
    for r in rows:
        agg[r["host_ip"]] = max(int(r["unique_dst_ports"]), agg.get(r["host_ip"], 0))
    top = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)[:10]
    return jsonify([{"host_ip": h, "unique_dst_ports": p} for h, p in top])


@bp.route("/new_source_spike")
def new_source_spike():
    rows = run_sql("new_source_spike.sql")
    return jsonify([
        {
            "host_ip": r["host_ip"],
            "interval_start": r["interval_start"].isoformat(),
            "unique_src_ips": int(r["unique_src_ips"]),
            "prev_src_ips": int(r["prev_src_ips"]),
            "new_src_jump": int(r["new_src_jump"]),
        }
        for r in rows
    ])


@bp.route("/rolling_pkt_30m_total")
def rolling_pkt_30m_total():
    rows = run_sql("rolling_30_min_pkt_count.sql")
    totals: Dict[str, int] = {}
    for r in rows:
        ts = r["interval_end"] 
        totals[ts] = totals.get(ts, 0) + int(r["pkts_last_30m"])
    return jsonify([{"interval_end": t, "total_pkts": totals[t]} for t in sorted(totals)])
