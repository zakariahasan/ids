
"""Linear SVM URL classification model (optimised for large datasets).

Shared upgrades
---------------
* Cap TF‑IDF to 50 000 char 3‑5‑grams (memory‑safe).
* Progress timing logs so training doesn’t appear “stuck”.
* Confusion‑matrix PNG & held‑out test metrics.
* Unified *models/* directory and clean `.load()`.
* CLI `--csv` argument.

Expected CSV columns: **url**, **type**
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Sequence

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
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
# Model
# ----------------------------------------------------------------------
class LinearSVMURLModel(BaseClassifierModel):
    """Linear Support‑Vector‑Machine URL classifier."""

    def __init__(self, **clf_kwargs):
        self.vectorizer = TfidfVectorizer(
            analyzer="char", ngram_range=(3, 5), max_features=50_000
        )
        default_params = {'C': 1.0, 'class_weight': 'balanced', 'random_state': 42}
        default_params.update(clf_kwargs)
        self.classifier = LinearSVC(**default_params)
        self._pipeline = Pipeline([
            ("vect", self.vectorizer),
            ("clf",  self.classifier),
        ])

    @property
    def model_path(self) -> Path:
        return MODEL_DIR / "linear_svm.pkl"

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
        raise NotImplementedError("LinearSVC does not support predict_proba")


    def train_and_plot(self, X: Sequence[str], y: Sequence[str], *, save_dir: Path) -> Path:
        save_dir.mkdir(parents=True, exist_ok=True)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, stratify=y, random_state=42
        )
        self.train(X_train, y_train)
        preds = self.predict(X_test)

        cm = confusion_matrix(y_test, preds, labels=np.unique(y))
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=np.unique(y))
        fig, ax = plt.subplots(figsize=(6, 5))
        disp.plot(ax=ax, cmap="Blues", colorbar=False)
        ax.set_title("Linear SVM – Confusion Matrix")
        plt.tight_layout()
        png_path = save_dir / "linear_svm_confusion_matrix.png"
        fig.savefig(png_path, dpi=150)
        plt.close(fig)

        print("\n[TEST‑SET METRICS]\n", classification_report(y_test, preds))
        print(f"[INFO] Confusion matrix saved to {png_path}")
        return png_path

    @classmethod
    def load(cls):
        pipeline = joblib.load(MODEL_DIR / "linear_svm.pkl")
        instance = cls.__new__(cls)  # type: ignore
        instance._pipeline = pipeline
        return instance

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train Linear SVM URL model")
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
    model.train_and_plot(df["url"], df["type"], save_dir=csv_path.parent)
