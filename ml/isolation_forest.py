"""Isolation Forest anomaly detection model wrapper."""
from pathlib import Path
import datetime as dt

import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from mpl_toolkits.mplot3d import Axes3D
from ids.core import config
from .base import BaseAnomalyModel

class IsolationForestModel(BaseAnomalyModel):
    """Isolation‑Forest based anomaly detector.

    * Fits a scaler ➜ IsolationForest on training data.
    * Persists model & scaler to ``config.MODEL_DIR``.
    * Provides helpers to score new samples and create a diagnostic plot.
    """

    def __init__(self, *, n_estimators: int = 100, contamination: float = 0.01, random_state: int = 42):
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self._model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state,
        )
        self._scaler = StandardScaler()

    # ------------------------------------------------------------------
    # Helper paths
    # ------------------------------------------------------------------
    @property
    def model_path(self) -> Path:
        return config.MODEL_DIR / "isolation_forest.pkl"

    # ------------------------------------------------------------------
    # Core API (implements BaseAnomalyModel contract)
    # ------------------------------------------------------------------
    def train(self, X: np.ndarray) -> None:
        """Fit scaler and IsolationForest on *X* (shape: [n_samples, n_features])."""
        X_scaled = self._scaler.fit_transform(X)
        self._model.fit(X_scaled)
        joblib.dump({"scaler": self._scaler, "model": self._model}, self.model_path)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores (higher = more normal)."""
        X_scaled = self._scaler.transform(X)
        return self._model.decision_function(X_scaled)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return labels (1 = inlier, ‑1 = anomaly)."""
        X_scaled = self._scaler.transform(X)
        return self._model.predict(X_scaled)

    def train_and_plot(self, X: np.ndarray, *, save_dir: Path) -> Path:
        save_dir.mkdir(parents=True, exist_ok=True)
        self.train(X)
        preds = self.predict(X)

        # Assume X has at least 3 features
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        normal = X[preds == 1]
        anomaly = X[preds == -1]
        ax.scatter(normal[:, 0], normal[:, 1], normal[:, 2], c='g', label='Normal', s=10)
        ax.scatter(anomaly[:, 0], anomaly[:, 1], anomaly[:, 2], c='r', label='Anomaly', s=30, marker='x')
        ax.set_xlabel("Packet Rate")
        ax.set_ylabel("Unique Port Count")
        ax.set_zlabel("Avg Packet Size")
        ax.set_title("Isolation Forest - Anomaly Detection (Training Data)")
        ax.legend()

        outfile = save_dir / f"isolation_forest_3d_{dt.datetime.utcnow():%Y%m%dT%H%M%S}.png"
        fig.tight_layout()
        fig.savefig(outfile)
        plt.close(fig)
        return outfile