"""One‑Class SVM anomaly detection model wrapper."""
from pathlib import Path
import datetime as dt

import joblib
import matplotlib.pyplot as plt
import numpy as np
from sklearn import svm
from sklearn.preprocessing import StandardScaler

from ids.core import config
from .base import BaseAnomalyModel

class OneClassSVMModel(BaseAnomalyModel):
    """One‑Class SVM detector using RBF kernel."""

    def __init__(self, *, nu: float = 0.01, gamma: str | float = "scale"):
        self.nu = nu
        self.gamma = gamma
        self._model = svm.OneClassSVM(nu=self.nu, kernel="rbf", gamma=self.gamma)
        self._scaler = StandardScaler()

    # ------------------------------------------------------------------
    @property
    def model_path(self) -> Path:
        return config.MODEL_DIR / "one_class_svm.pkl"

    # ------------------------------------------------------------------
    def train(self, X: np.ndarray) -> None:
        X_scaled = self._scaler.fit_transform(X)
        self._model.fit(X_scaled)
        joblib.dump({"scaler": self._scaler, "model": self._model}, self.model_path)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self._scaler.transform(X)
        return self._model.score_samples(X_scaled)  # higher = more normal

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self._scaler.transform(X)
        return self._model.predict(X_scaled)  # 1 inlier, ‑1 outlier

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
        ax.set_title("One Class SVM - Anomaly Detection (Training Data)")
        ax.legend()

        outfile = save_dir / f"one_class_svm_3d_{dt.datetime.utcnow():%Y%m%dT%H%M%S}.png"
        fig.tight_layout()
        fig.savefig(outfile)
        plt.close(fig)
        return outfile