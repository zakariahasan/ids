"""
ids.web.alerts – DB-agnostic implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
✓ Works with Postgres *and* SQLite
✓ Uses the shared DatabaseService  (ids.core.db_provider.get_database_service)
✓ No direct cursor access – one abstraction point
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
from ids.core.db_provider import get_database_service

bp = Blueprint("alerts", __name__, url_prefix="/alerts")

URL_MODELS = {"DecisionTree", "RandomForest", "LinearSVM"}
BEHAV_MODELS = {"IsolationForest", "Autoencoder", "OneClassSVM"}
MODEL_FILE = Path(config.BASE_DIR) / "current_model.txt"

# ------------------------------------------------------------------ #
# DB helpers                                                         #
# ------------------------------------------------------------------ #
def _fetch_recent_alerts(limit: int = 10) -> List[dict[str, Any]]:
    """Return the *limit* most-recent alerts as a list of dicts."""
    db = get_database_service()

    # The service already returns list[dict], so no post-processing needed
    sql = (
        "SELECT alert_id, ts, alert_type, src_ip, dst_ip, "
        "details, model_name "
        "FROM alerts "
        "ORDER BY ts DESC "
        f"LIMIT {int(limit)}"  # safe – limit is integer in our code path
    )
    return db.execute_query(sql)


# ------------------------------------------------------------------ #
# Helper for model selection                                         #
# ------------------------------------------------------------------ #
def _current_model() -> str:
    return MODEL_FILE.read_text().strip() if MODEL_FILE.exists() else "DecisionTree"


def _persist_model(choice: str) -> None:
    MODEL_FILE.write_text(choice)


# ------------------------------------------------------------------ #
# Routes                                                              #
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
