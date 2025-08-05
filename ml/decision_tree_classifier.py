
"""Decision Tree URL classification model (optimised for large datasets).

Key changes
-----------
* **Feature cap**: TF‑IDF `max_features=50 000` to bound RAM and fit‑time.
* **Regularised tree**: `max_depth=25`, `min_samples_leaf=5` – prevents huge trees.
* **Timing logs**: prints training duration so you see progress.
* **Unified MODEL_DIR**: sibling *models* directory, same as other models.
* **Cleaner `.load()`**: avoids building a dummy pipeline.
* **Held‑out metrics**: classification report is on the 30 % test split only.
* **CLI**: `python decision_tree_classifier.py --csv path/to/data.csv`

Columns expected in CSV: **url**, **type**
"""  # noqa: E501

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
from sklearn.tree import DecisionTreeClassifier

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
class DecisionTreeURLModel(BaseClassifierModel):
    """Decision Tree based supervised URL classifier."""  # noqa: D401

    def __init__(self, **clf_kwargs):
        self.vectorizer = TfidfVectorizer(
            analyzer="char",
            ngram_range=(3, 5),
            max_features=50_000,   # cap dimensionality
        )
        default_params = dict(max_depth=25, min_samples_leaf=5, random_state=42)
        default_params.update(clf_kwargs)
        self.classifier = DecisionTreeClassifier(**default_params)
        self._pipeline = Pipeline([
            ("vect", self.vectorizer),
            ("clf",  self.classifier),
        ])

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------
    @property
    def model_path(self) -> Path:
        return MODEL_DIR / "decision_tree.pkl"

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
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
        ax.set_title("Decision Tree – Confusion Matrix")
        plt.tight_layout()

        png_path = save_dir / "decision_tree_confusion_matrix.png"
        fig.savefig(png_path, dpi=150)
        plt.close(fig)

        print("\n[TEST‑SET METRICS]\n", classification_report(y_test, preds))
        print(f"[INFO] Confusion matrix saved to {png_path}")
        return png_path

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    @classmethod
    def load(cls):
        pipeline = joblib.load(MODEL_DIR / "decision_tree.pkl")
        instance = cls.__new__(cls)        # type: ignore
        instance._pipeline = pipeline
        return instance

# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train DecisionTree URL model")
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
    model = DecisionTreeURLModel()
    model.train_and_plot(df["url"], df["type"], save_dir=csv_path.parent)
