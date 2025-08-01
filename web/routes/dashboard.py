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
