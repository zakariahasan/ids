"""Flask blueprint for training SUPERVISED machine‑learning models.

URL prefix: /train/supervised
Templates: re‑uses *train_model.html*
Static results saved to: static/training_results/supervised
"""

from flask import Blueprint, render_template, request, flash, current_app
from ids.ml.factory import ModelFactory
from ids.core import config
import pandas as pd
from pathlib import Path
import re
from datetime import datetime


bp = Blueprint("train_supervised", __name__, url_prefix="/train/supervised")

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
_TIMESTAMP_RE = re.compile(r"_(\d{8}T\d{6})")


def _extract_timestamp(fname: str) -> datetime:
    m = _TIMESTAMP_RE.search(fname)
    return datetime.strptime(m.group(1), "%Y%m%dT%H%M%S") if m else datetime.min


def _latest_pngs(directory: Path, keep: int = 6) -> list[str]:
    files = [f.name for f in directory.iterdir() if f.suffix == ".png"]
    files.sort(key=_extract_timestamp, reverse=True)
    for stale in files[keep:]:
        try:
            (directory / stale).unlink()
        except Exception as exc:
            current_app.logger.warning("Could not delete %s: %s", stale, exc)
    return files[:keep]


# ----------------------------------------------------------------------
# Route
# ----------------------------------------------------------------------
@bp.route("/", methods=["GET", "POST"])
def train_supervised_model():
    training_dir = Path(current_app.root_path, "static", "training_results", "supervised")
    training_dir.mkdir(parents=True, exist_ok=True)

    recent_images = _latest_pngs(training_dir)

    supervised_models = {"DecisionTree", "RandomForest", "LinearSVM"}

    if request.method == "POST":
        model_name: str = request.form["model_type"]

        if model_name not in supervised_models:
            flash(f"{model_name} is not configured as a supervised model.", "error")
            return render_template("train_model.html", training_image=None, recent_images=recent_images)

        # Load labelled phishing dataset
        df = pd.read_csv(config.BASE_DIR / "data" / "malicious_phish.csv")
        X, y = df["url"], df["type"]

        model = ModelFactory.create(model_name)
        plot_path = model.train_and_plot(X, y, save_dir=training_dir)

        flash(f"{model_name} trained successfully.")
        recent_images.insert(0, plot_path.name)
        recent_images = recent_images[:6]

        return render_template("train_supervised.html", training_image=plot_path.name, recent_images=recent_images)

    # GET
    return render_template("train_supervised.html", training_image=None, recent_images=recent_images)
