"""Flask blueprint for training SUPERVISED machine‑learning models.

URL prefix: /train/supervised
Templates: re‑uses *train_model.html*
Static results saved to: static/training_results/supervised
"""

from flask import Blueprint, render_template, request, flash, current_app
from ids.ml.factory import ModelFactory
from ids.core import config
import pandas as pd
import numpy as np
from pathlib import Path
import re
import os
from datetime import datetime
# NEW ────────────────────────────────────────────────────────────────────────
from werkzeug.utils import secure_filename
import joblib, tempfile

bp = Blueprint("train_supervised", __name__, url_prefix="/train/supervised")

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
_TIMESTAMP_RE = re.compile(r"_(\d{8}T\d{6})")
#NEW
PICKLE_DIR = Path(config.BASE_DIR, "ml_models")          # where .pkl files live
PICKLE_DIR.mkdir(exist_ok=True)

_SUPPORTED = {"DecisionTree": "decision_tree.pkl",
              "RandomForest":  "random_forest.pkl",
              "LinearSVM":     "linear_svm.pkl"}

def _load_pipeline(model_name: str):
    """Return a sklearn Pipeline for *model_name* or raise FileNotFoundError."""
    pkl = PICKLE_DIR / _SUPPORTED[model_name]
    if not pkl.exists():
        raise FileNotFoundError(f"Train {model_name} first – {pkl.name} is missing")
    return joblib.load(pkl)

#NEW
def _extract_timestamp(fname: str) -> datetime:
    m = _TIMESTAMP_RE.search(fname)
    return datetime.strptime(m.group(1), "%Y%m%dT%H%M%S") if m else datetime.min


def _latest_pngs(folder: Path, limit: int = 6) -> list[str]:
    """Return up-to-date list of PNG filenames, newest first."""
    return sorted((p.name for p in folder.glob("*.png")),
                  key=lambda n: os.path.getmtime(folder / n),
                  reverse=True)[:limit]


# ----------------------------------------------------------------------
# Route
# ----------------------------------------------------------------------
# imports – add secure_filename for safety
from werkzeug.utils import secure_filename
import tempfile

@bp.route("/", methods=["GET", "POST"])
def train_supervised_model():
    training_dir = Path(current_app.root_path,
                        "static", "training_results", "supervised")
    training_dir.mkdir(parents=True, exist_ok=True)

    recent_images = _latest_pngs(training_dir)
    supervised_models = {"DecisionTree", "RandomForest", "LinearSVM"}

    if request.method == "POST":
        model_name: str = request.form["model_type"]

        # 1️⃣ ---------- validate model -------------------------------------
        if model_name not in supervised_models:
            flash(f"{model_name} is not configured as a supervised model.", "error")
            return render_template("train_supervised.html",
                                   training_image=None, recent_images=recent_images)

        # 2️⃣ ---------- DATA SOURCE ----------------------------------------
        file_obj = request.files.get("csv_file")          # ← new
        if file_obj and file_obj.filename:
            fname = secure_filename(file_obj.filename)
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
                file_obj.save(tmp.name)
                csv_path = Path(tmp.name)

            flash(f"Custom dataset “{fname}” uploaded.", "info")
        else:
            # fall-back to the default dataset
            csv_path = config.BASE_DIR / "data" / "malicious_phish.csv"
            flash("No file chosen – using bundled malicious_phish.csv", "warning")

        # 3️⃣ ---------- LOAD + TRAIN ---------------------------------------
        df = pd.read_csv(csv_path)
        X, y = df["url"], df["type"]

        model = ModelFactory.create(model_name)
        plot_path = model.train_and_plot(X, y, save_dir=training_dir)

        flash(f"{model_name} trained successfully.")
        recent_images.insert(0, plot_path.name)
        recent_images = recent_images[:6]

        return render_template("train_supervised.html",
                               training_image=plot_path.name,
                               recent_images=recent_images)

    # GET
    return render_template("train_supervised.html",
                           training_image=None, recent_images=recent_images)
# ─────────────────────────  NEW PREDICTION END-POINT  ──────────────────────
@bp.route("/predict", methods=["GET", "POST"])
def predict_url_type():
    """Simple form → predict URL category with a previously-trained model."""
    prediction, proba = None, None
    models = list(_SUPPORTED.keys())

    if request.method == "POST":
        model_name = request.form["model_type"]
        url_value  = request.form["url"].strip()

        try:
            pipe = _load_pipeline(model_name)
            proba = pipe.predict_proba([url_value])[0]
            prediction = pipe.classes_[np.argmax(proba)]
            proba = dict(zip(pipe.classes_, proba.round(3)))
        except FileNotFoundError as exc:
            flash(str(exc), "error")
        except Exception as exc:
            current_app.logger.exception(exc)
            flash("Prediction failed – see server logs.", "error")
    training_dir = Path(current_app.root_path,
                        "static", "training_results", "supervised")
    recent_images = _latest_pngs(training_dir)
    return render_template(
        "train_supervised.html",           # reuse template
        show_predict=True,                 # toggle second tab
        prediction=prediction,
        proba=proba,
        models=models,
        recent_images=recent_images,
    )