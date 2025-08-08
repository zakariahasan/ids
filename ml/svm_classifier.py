"""Linear SVM URL classification model (optimised for large datasets).

Shared upgrades
---------------
* Cap TF‑IDF to 50 000 char 3‑5‑grams (memory‑safe).
* Progress timing logs so training doesn’t appear “stuck”.
* Confusion‑matrix & ROC‑AUC PNG exports plus held‑out test metrics.
* Unified *models/* directory and clean `.load()`.
* CLI `--csv` argument.

Expected CSV columns: **url**, **type**
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Sequence
import datetime as dt

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (ConfusionMatrixDisplay, RocCurveDisplay, auc,
                             classification_report, confusion_matrix, roc_curve)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import label_binarize
from sklearn.svm import LinearSVC

# ----------------------------------------------------------------------
# Local imports
# ----------------------------------------------------------------------
try:
    from ids.core import config  # type: ignore
    MODEL_DIR = config.MODEL_DIR
except Exception:
    MODEL_DIR = Path(__file__).resolve().parent / "models"
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

try:
    from base_classifier import BaseClassifierModel
except ImportError:
    from .base_classifier import BaseClassifierModel  # type: ignore

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _plot_and_save(fig, save_dir: Path, name: str) -> Path:
    """Save matplotlib *fig* to *save_dir* with a UTC timestamped filename."""
    save_dir.mkdir(parents=True, exist_ok=True)
    png_path = save_dir / f"{name}_{dt.datetime.utcnow():%Y%m%dT%H%M%S}.png"
    fig.savefig(png_path, dpi=150)
    plt.close(fig)
    print(f"[INFO] {name.replace('_', ' ').title()} saved to {png_path}")
    return png_path

# ----------------------------------------------------------------------
# Model
# ----------------------------------------------------------------------
class LinearSVMURLModel(BaseClassifierModel):
    """Linear Support‑Vector‑Machine URL classifier with ROC‑AUC visualisation."""

    def __init__(self, **clf_kwargs):
        self.vectorizer = TfidfVectorizer(
            analyzer="char", ngram_range=(3, 5), max_features=50_000
        )
        default_params = {"C": 1.0, "class_weight": "balanced", "random_state": 42}
        default_params.update(clf_kwargs)
        self.classifier = LinearSVC(**default_params)
        self._pipeline = Pipeline([
            ("vect", self.vectorizer),
            ("clf", self.classifier),
        ])

    # ----------------------------- Properties -----------------------------
    @property
    def model_path(self) -> Path:
        return MODEL_DIR / "linear_svm.pkl"

    # --------------------------- Core methods -----------------------------
    def train(self, X: Sequence[str], y: Sequence[str]) -> None:
        tic = time.perf_counter()
        print("[INFO] Training started…", flush=True)
        self._pipeline.fit(X, y)
        toc = time.perf_counter()
        print(f"[INFO] Training finished in {toc - tic:,.1f}s", flush=True)
        joblib.dump(self._pipeline, self.model_path, compress=3)

    def predict(self, X: Sequence[str]):
        return self._pipeline.predict(X)

    def _decision_function(self, X: Sequence[str]):
        """Return decision scores from the underlying LinearSVC."""
        return self._pipeline.decision_function(X)

    def predict_proba(self, X: Sequence[str]):
        raise NotImplementedError("LinearSVC does not support predict_proba – use decision_function() for scores")

    # ----------------------- Evaluation utilities -------------------------
    def _plot_confusion_matrix(self, y_true, y_pred, labels, save_dir: Path) -> Path:
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
        fig, ax = plt.subplots(figsize=(6, 5))
        disp.plot(ax=ax, cmap="Blues", colorbar=False)
        ax.set_title("Linear SVM – Confusion Matrix")
        plt.tight_layout()
        return _plot_and_save(fig, save_dir, "linear_svm_confusion_matrix")

    def _plot_roc_auc(self, y_true, scores, classes, save_dir: Path) -> Path:
        """Plot ROC curve(s) and compute AUC for binary or multi‑class tasks."""
        fig, ax = plt.subplots(figsize=(6, 5))

        if len(classes) == 2:  # Binary
            fpr, tpr, _ = roc_curve(y_true, scores)
            roc_auc = auc(fpr, tpr)
            RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc, estimator_name="Linear SVM").plot(ax=ax)
            ax.set_title(f"ROC Curve (AUC = {roc_auc:.3f}) – Binary")
        else:
            # Multi‑class One‑Vs‑Rest scheme
            y_true_bin = label_binarize(y_true, classes=classes)
            if scores.ndim == 1:
                scores = scores[:, np.newaxis]
            # Compute per‑class ROC
            for idx, cls in enumerate(classes):
                fpr, tpr, _ = roc_curve(y_true_bin[:, idx], scores[:, idx])
                roc_auc = auc(fpr, tpr)
                RocCurveDisplay(
                    fpr=fpr,
                    tpr=tpr,
                    roc_auc=roc_auc,
                    estimator_name=f"Class {cls}"
                ).plot(ax=ax, alpha=0.8, lw=1)
            # Micro‑average
            fpr_micro, tpr_micro, _ = roc_curve(y_true_bin.ravel(), scores.ravel())
            roc_auc_micro = auc(fpr_micro, tpr_micro)
            RocCurveDisplay(
                fpr=fpr_micro,
                tpr=tpr_micro,
                roc_auc=roc_auc_micro,
                estimator_name="micro‑avg"
            ).plot(ax=ax, color="black", linestyle="--", lw=2)
            ax.set_title("ROC Curves – Multi‑class (micro‑avg shown dashed)")

        ax.grid(True, ls=":", lw=0.5)
        plt.tight_layout()
        return _plot_and_save(fig, save_dir, "linear_svm_roc_auc")

    # ------------------------ Public interface ---------------------------
    def train_and_plot(self, X: Sequence[str], y: Sequence[str], *, save_dir: Path) -> tuple[Path, Path]:
        """Train‑test split, train the model and export Confusion Matrix & ROC‑AUC plots.

        Returns
        -------
        tuple(Path, Path)
            Paths to the confusion‑matrix PNG and ROC‑AUC PNG respectively.
        """
        save_dir.mkdir(parents=True, exist_ok=True)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, stratify=y, random_state=42
        )
        # --------------------- Train & predict ---------------------
        self.train(X_train, y_train)
        preds = self.predict(X_test)
        scores = self._decision_function(X_test)

        # ----------------- Visualisations & metrics ----------------
        classes = np.unique(y)
        cm_png = self._plot_confusion_matrix(y_test, preds, classes, save_dir)
        roc_png = self._plot_roc_auc(y_test, scores, classes, save_dir)

        # Text metrics
        print("\n[TEST‑SET METRICS]\n", classification_report(y_test, preds))
        return cm_png, roc_png

    # ----------------------------- Utilities -----------------------------
    @classmethod
    def load(cls):
        pipeline = joblib.load(MODEL_DIR / "linear_svm.pkl")
        instance = cls.__new__(cls)  # type: ignore
        instance._pipeline = pipeline
        return instance

# ----------------------------------------------------------------------
# CLI helper
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train Linear SVM URL model and export metrics")
    parser.add_argument(
        "--csv",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "data/malicious_phish.csv"),
        help="CSV with 'url' and 'type' columns",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    df = pd.read_csv(csv_path)
    
    model = LinearSVMURLModel()
    cm_png, roc_png = model.train_and_plot(df["url"], df["type"], save_dir=csv_path.parent)
    #print(f"\nConfusion-matrix → {cm_png}")
    #print(f"ROC curve       → {roc_png}")