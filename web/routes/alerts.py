
"""
ids.web.alerts  – updated fallback uses DatabaseClient._get_conn_cursor()
avoiding direct access to `.conn`
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from ids.core import config

bp = Blueprint("alerts", __name__, url_prefix="/alerts")

URL_MODELS = {"DecisionTree", "RandomForest", "LinearSVM"}
BEHAV_MODELS = {"IsolationForest", "Autoencoder", "OneClassSVM"}
MODEL_FILE = Path(config.BASE_DIR) / "current_model.txt"


# ------------------------------------------------------------------ #
# DB helpers                                                         #
# ------------------------------------------------------------------ #
def _lazy_db():
    from importlib import import_module

    return import_module("ids.core.db").db  # type: ignore[attr-defined]


def _dictify(rows):
    if not rows:
        return []
    if hasattr(rows[0], "keys"):
        return [dict(r) for r in rows]
    return [
        dict(
            alert_id=r[0],
            ts=r[1],
            alert_type=r[2],
            src_ip=r[3],
            dst_ip=r[4],
            details=r[5],
            model_name=r[6],
        )
        for r in rows
    ]


def _fetch_recent_alerts(limit: int = 10) -> List[dict[str, Any]]:
    db = _lazy_db()

    # Preferred helper
    if hasattr(db, "fetch_alerts"):
        return _dictify(db.fetch_alerts(limit))  # type: ignore[attr-defined]

    # Generic query helper
    if hasattr(db, "query"):
        rows = db.query(
            """SELECT alert_id, ts, alert_type, src_ip, dst_ip,
                       details, model_name
                  FROM alerts
                  ORDER BY ts DESC
                  LIMIT %s""",
            (limit,),
        )
        return _dictify(rows)

    # FINAL fallback – use the private _get_conn_cursor
    if hasattr(db, "_get_conn_cursor"):
        with db._get_conn_cursor() as (_conn, cur):  # type: ignore[attr-defined]
            cur.execute(
                """SELECT alert_id, ts, alert_type, src_ip, dst_ip,
                           details, model_name
                      FROM alerts
                      ORDER BY ts DESC
                      LIMIT %s""",
                (limit,),
            )
            return _dictify(cur.fetchall())

    # If we reach here, database layer is too restricted
    return []


# ------------------------------------------------------------------ #
# Helper for model selection
# ------------------------------------------------------------------ #
def _current_model() -> str:
    return MODEL_FILE.read_text().strip() if MODEL_FILE.exists() else "DecisionTree"


def _persist_model(choice: str) -> None:
    MODEL_FILE.write_text(choice)


# ------------------------------------------------------------------ #
# Route
# ------------------------------------------------------------------ #
@bp.route("/", methods=["GET", "POST"])
def alert_dashboard():
    if request.method == "POST":
        choice = request.form["model_choice"]
        if choice not in URL_MODELS | BEHAV_MODELS:
            flash("Unknown model selected", "error")
            return redirect(url_for(".alert_dashboard"))

        _persist_model(choice)
        flash(f"Detection model switched to {choice}", "success")
        return redirect(url_for(".alert_dashboard"))

    alerts = _fetch_recent_alerts()

    return render_template(
        "alert_activity.html",
        alerts=alerts,
        current_model=_current_model(),
        url_models=sorted(URL_MODELS),
        behaviour_models=sorted(BEHAV_MODELS),
    )
