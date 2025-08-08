"""Random Forest URL classification model (optimised for large datasets).

Adds ROC–AUC visualisation alongside the existing confusion‑matrix export.

Expected CSV columns: **url**, **type**
"""

from __future__ import annotations

import datetime as dt
import time
from pathlib import Path
from typing import Sequence

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    auc,
    classification_report,
    confusion_matrix,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import label_binarize

# ----------------------------------------------------------------------
# Local imports / fallbacks
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
# Helper utilities (shared)
# ----------------------------------------------------------------------

def _plot_and_save(fig, save_dir: Path, name: str) -> Path:
    """Save *fig* as *name*_<UTCtimestamp>.png inside *save_dir* and close fig."""
    save_dir.mkdir(parents=True, exist_ok=True)
    png_path = save_dir / f"{name}_{dt.datetime.utcnow():%Y%m%dT%H%M%S}.png"
    fig.savefig(png_path, dpi=150)
    plt.close(fig)
    print(f"[INFO] {name.replace('_', ' ').title()} saved to {png_path}")
    return png_path

# ----------------------------------------------------------------------
# Model
# ----------------------------------------------------------------------
class RandomForestURLModel(BaseClassifierModel):
    """Random‑Forest ensemble URL classifier with ROC–AUC plots."""

    def __init__(self, **clf_kwargs):
        self.vectorizer = TfidfVectorizer(
            analyzer="char", ngram_range=(3, 5), max_features=50_000
        )
        default_params = {
            "n_estimators": 300,
            "max_depth": 30,
            "min_samples_leaf": 3,
            "n_jobs": -1,
            "random_state": 42,
        }
        default_params.update(clf_kwargs)
        self.classifier = RandomForestClassifier(**default_params)
        self._pipeline = Pipeline([
            ("vect", self.vectorizer),
            ("clf", self.classifier),
        ])

    # -------------------------- Properties --------------------------
    @property
    def model_path(self) -> Path:
        return MODEL_DIR / "random_forest.pkl"

    # -------------------------- Core API ----------------------------
    def train(self, X: Sequence[str], y: Sequence[str]) -> None:
        tic = time.perf_counter()
        print("[INFO] Training started…", flush=True)
        self._pipeline.fit(X, y)
        toc = time.perf_counter()
        print(f"[INFO] Training finished in {toc - tic:,.1f}s", flush=True)
        joblib.dump(self._pipeline, self.model_path, compress=3)

    def predict(self, X: Sequence[str]):
        return self._pipeline.predict(X)

    def predict_proba(self, X: Sequence[str]):
        return self._pipeline.predict_proba(X)

    # -------------------- Private visual helpers --------------------
    def _plot_confusion_matrix(self, y_true, y_pred, labels, save_dir: Path) -> Path:
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
        fig, ax = plt.subplots(figsize=(6, 5))
        disp.plot(ax=ax, cmap="Blues", colorbar=False)
        ax.set_title("Random Forest – Confusion Matrix")
        plt.tight_layout()
        return _plot_and_save(fig, save_dir, "random_forest_confusion_matrix")

    def _plot_roc_auc(self, y_true, probs, classes, save_dir: Path) -> Path:
        """Generate ROC curve(s) & AUC for binary or multi‑class problems."""
        fig, ax = plt.subplots(figsize=(6, 5))

        # ---------------------- Binary case ----------------------
        if len(classes) == 2:
            # Probability of the positive class (column index 1 when classes are sorted)
            positive_class_idx = list(classes).index(classes[1])
            fpr, tpr, _ = roc_curve(y_true, probs[:, positive_class_idx], pos_label=classes[1])
            roc_auc = auc(fpr, tpr)
            RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc, estimator_name="Random Forest").plot(ax=ax)
            ax.set_title(f"ROC Curve (AUC = {roc_auc:.3f}) – Binary")

        # -------------------- Multi‑class OVR ---------------------
        else:
            y_true_bin = label_binarize(y_true, classes=classes)
            # Compute one‑vs‑rest curves
            for idx, cls in enumerate(classes):
                fpr, tpr, _ = roc_curve(y_true_bin[:, idx], probs[:, idx])
                roc_auc = auc(fpr, tpr)
                RocCurveDisplay(
                    fpr=fpr,
                    tpr=tpr,
                    roc_auc=roc_auc,
                    estimator_name=f"Class {cls}",
                ).plot(ax=ax, lw=1, alpha=0.8)
            # Micro‑average curve
            fpr_micro, tpr_micro, _ = roc_curve(y_true_bin.ravel(), probs.ravel())
            roc_auc_micro = auc(fpr_micro, tpr_micro)
            RocCurveDisplay(
                fpr=fpr_micro,
                tpr=tpr_micro,
                roc_auc=roc_auc_micro,
                estimator_name="micro‑avg",
            ).plot(ax=ax, color="black", linestyle="--", lw=2)
            ax.set_title("ROC Curves – Multi‑class (micro‑avg dashed)")

        ax.grid(True, ls=":", lw=0.5)
        plt.tight_layout()
        return _plot_and_save(fig, save_dir, "random_forest_roc_auc")

    # -------------------- High‑level convenience ------------------
    def train_and_plot(self, X: Sequence[str], y: Sequence[str], *, save_dir: Path) -> tuple[Path, Path]:
        """Train‑test split, train the model, export Confusion Matrix & ROC‑AUC plots.

        Returns
        -------
        (cm_png, roc_png): tuple[Path, Path]
            Paths to the confusion‑matrix PNG and ROC‑AUC PNG respectively.
        """
        save_dir.mkdir(parents=True, exist_ok=True)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, stratify=y, random_state=42
        )

        # ---------------- Train & predict ----------------
        self.train(X_train, y_train)
        preds = self.predict(X_test)
        probs = self.predict_proba(X_test)

        # -------------- Visualisations --------------
        classes = np.unique(y)
        cm_png = self._plot_confusion_matrix(y_test, preds, classes, save_dir)
        roc_png = self._plot_roc_auc(y_test, probs, classes, save_dir)

        # -------------- Text metrics ----------------
        print("\n[TEST‑SET METRICS]\n", classification_report(y_test, preds))
        return cm_png, roc_png

    # ---------------------- Loader ------------------------
    @classmethod
    def load(cls):
        pipeline = joblib.load(MODEL_DIR / "random_forest.pkl")
        instance = cls.__new__(cls)  # type: ignore
        instance._pipeline = pipeline
        return instance

# ----------------------------------------------------------------------
# CLI helper
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Train Random Forest URL model and export Confusion‑Matrix + ROC‑AUC plots"
    )
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
    model = RandomForestURLModel()
    cm_png, roc_png = model.train_and_plot(df["url"], df["type"], save_dir=csv_path.parent)
    print(f"\nSaved Confusion‑Matrix → {cm_png}\nSaved ROC‑AUC curve   → {roc_png}")