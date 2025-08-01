from flask import Blueprint, render_template, jsonify, current_app
from sqlalchemy import text
from pathlib import Path
from ids.web.extensions import db
bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')
QUERY_DIR = Path(__file__).resolve().parent.parent.parent / 'queries'

def run_sql(file_name):
    sql = (QUERY_DIR / file_name).read_text()
    rows = db.session.execute(text(sql)).mappings()
    return [dict(r) for r in rows]

@bp.route('/')
def view():
    return render_template('dashboard.html')

@bp.route('/top_hosts')
def api_top_hosts():
    return jsonify(run_sql('host_count.sql'))

@bp.route("/alerts_by_hour")
def alerts_by_hour():
    rows = run_sql('alerts_by_hour.sql')
    buckets = {}
    for row in rows:
        hour = row["hour_bucket"].strftime("%Y-%m-%d %H:%M")
        buckets.setdefault(hour, {})[row["alert_type"]] = row["alert_cnt"]
    return jsonify(buckets)

@bp.route("/top_sources")
def top_sources():
    return jsonify(run_sql('top_sources.sql'))

@bp.route("/ddos_last_10m")
def ddos_last_10m():
    rows = run_sql('ddos_last_10m.sql')
    return jsonify([
        {
            "timestamp": r["ts"].isoformat(),
            "count": r["ddos_window"],
        } for r in rows
    ])

@bp.route("/scan_bursts")
def scan_bursts():
    rows = run_sql('scan_bursts.sql')
    return jsonify([
        {
            "src_ip": r["src_ip"],
            "burst_start": r["burst_start"].isoformat(),
            "burst_end": r["burst_end"].isoformat(),
            "scans": r["scans_in_burst"],
        } for r in rows
    ])
@bp.route("/top_bandwidth")
def top_bandwidth():
    """
    Five hosts that moved the most bytes in the last 10 minutes.
    Also returns packet counts so the UI can plot both.
    """
    rows = run_sql("top_bandwidth_taker.sql")
    # Make sure JSON is clean ints (SqlAlchemy may return Decimal)
    for r in rows:
        r["bytes_last_10m"] = int(r["bytes_last_10m"])
        r["pkts_last_10m"]  = int(r["pkts_last_10m"])
    return jsonify(rows)
    
# ──────────────────────────────────────────────────────────────────────
# NEW #2 – Average packet size per host (all-time)
# ──────────────────────────────────────────────────────────────────────
@bp.route("/avg_pkt_size")
def avg_pkt_size():
    """
    Average packet size (bytes) and total packet count per host, lifetime.
    Backed by avg_pkt_size_per_host.sql.
    """
    rows = run_sql("avg_pkt_size_per_host.sql")  # uses host_ip, avg_pkt_size_bytes, total_pkts
    # Cast to JSON-friendly types
    for r in rows:
        r["avg_pkt_size_bytes"] = float(r["avg_pkt_size_bytes"])
        r["total_pkts"]         = int(r["total_pkts"])
    return jsonify(rows)
    
# ──────────────────────────────────────────────────────────────────────
# NEW #3 – Hosts with heavy outgoing bias (last hour)
# ──────────────────────────────────────────────────────────────────────
@bp.route("/heavy_outgoing")
def heavy_outgoing():
    """
    Hosts whose outgoing packets ≥ 2 × incoming in the past hour.
    Returns in_pkts, out_pkts, and out_in_ratio.
    """
    rows = run_sql("host_with_heavy_outgoing.sql")  # :contentReference[oaicite:1]{index=1}
    for r in rows:
        r["in_pkts"]       = int(r["in_pkts"])
        r["out_pkts"]      = int(r["out_pkts"])
        r["out_in_ratio"]  = float(r["out_in_ratio"])
    return jsonify(rows)
# ──────────────────────────────────────────────────────────────────────
# NEW – Port fan-out check (unique dst ports, last 2 h)
# ──────────────────────────────────────────────────────────────────────
@bp.route("/port_fanout")
def port_fanout():
    """
    Return up to 10 hosts that have contacted the widest range of dst ports
    in the past two hours.
    """
    rows = run_sql("port_fan_out_check.sql")        # :contentReference[oaicite:1]{index=1}

    # Aggregate per-host (SQL may return multiple intervals per host).
    agg: dict[str, int] = {}
    for r in rows:
        host = r["host_ip"]
        ports = int(r["unique_dst_ports"])
        agg[host] = max(ports, agg.get(host, 0))

    top = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)[:10]
    return jsonify([{"host_ip": h, "unique_dst_ports": p} for h, p in top])
# ──────────────────────────────────────────────────────────────────────
# NEW – new-source spike (possible DDoS precursor)
# ──────────────────────────────────────────────────────────────────────
@bp.route("/new_source_spike")
def new_source_spike():
    """
    Returns every interval (past 12 h) where a host suddenly saw ≥10 new
    source IPs compared with the previous interval.
    """
    rows = run_sql("new_source_spike.sql")

    # Force JSON-friendly types & ISO timestamp strings
    cleaned = []
    for r in rows:
        cleaned.append({
            "host_ip":          r["host_ip"],
            "interval_start":   r["interval_start"].isoformat(),
            "unique_src_ips":   int(r["unique_src_ips"]),
            "prev_src_ips":     int(r["prev_src_ips"]),
            "new_src_jump":     int(r["new_src_jump"]),
        })
    return jsonify(cleaned)
# ──────────────────────────────────────────────────────────────────────
# NEW – rolling 30-minute packet count (past 24 h)
# ──────────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────
# NEW – total packets across all hosts per 30-min window (past 24 h)
# ──────────────────────────────────────────────────────────────────────
@bp.route("/rolling_pkt_30m_total")
def rolling_pkt_30m_total():
    rows = run_sql("rolling_30_min_pkt_count.sql")

    totals: dict[str, int] = {}
    for r in rows:
        ts = r["interval_end"].isoformat()
        totals[ts] = totals.get(ts, 0) + int(r["pkts_last_30m"])

    # sort chronologically
    series = [{"interval_end": t, "total_pkts": totals[t]} 
              for t in sorted(totals)]
    return jsonify(series)