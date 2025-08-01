"""Autoencoder‑based anomaly detection model wrapper."""
from pathlib import Path
import datetime as dt

import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import StandardScaler
from tensorflow import keras
from tensorflow.keras import layers

from ids.core import config
from .base import BaseAnomalyModel

class AutoencoderModel(BaseAnomalyModel):
    """Denoising autoencoder for anomaly detection.

    * Learns to reconstruct normal traffic samples.
    * Reconstruction error > threshold ➜ anomaly.
    * Saves Keras model (.keras) + scaler (.pkl).
    """

    def __init__(self, *, encoding_dim: int = 16, epochs: int = 20, batch_size: int = 256):
        self.encoding_dim = encoding_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self._scaler = StandardScaler()
        self._model = None  # built during train

    # ------------------------------------------------------------------
    @property
    def model_path(self) -> Path:
        return config.MODEL_DIR / "autoencoder.keras"

    @property
    def scaler_path(self) -> Path:
        return config.MODEL_DIR / "autoencoder_scaler.pkl"

    # ------------------------------------------------------------------
    def _build_model(self, n_features: int):
        input_layer = layers.Input(shape=(n_features,))
        x = layers.Dense(self.encoding_dim, activation="relu")(input_layer)
        x = layers.Dense(int(self.encoding_dim / 2), activation="relu")(x)
        x = layers.Dense(self.encoding_dim, activation="relu")(x)
        output_layer = layers.Dense(n_features, activation="linear")(x)
        model = keras.Model(input_layer, output_layer)
        model.compile(optimizer="adam", loss="mse")
        return model

    # ------------------------------------------------------------------
    def train(self, X: np.ndarray) -> None:
        X_scaled = self._scaler.fit_transform(X)
        n_features = X_scaled.shape[1]
        self._model = self._build_model(n_features)
        self._model.fit(
            X_scaled,
            X_scaled,
            epochs=self.epochs,
            batch_size=self.batch_size,
            shuffle=True,
            verbose=0,
        )
        self._model.save(self.model_path)
        joblib.dump(self._scaler, self.scaler_path)

    def reconstruction_error(self, X: np.ndarray) -> np.ndarray:
        X_scaled = self._scaler.transform(X)
        preds = self._model.predict(X_scaled, verbose=0)
        return np.mean(np.square(preds - X_scaled), axis=1)

    def predict(self, X: np.ndarray, threshold: float = None):
        """Return 1 for normal, ‑1 for anomaly using *threshold* (auto if None)."""
        errors = self.reconstruction_error(X)
        if threshold is None:
            threshold = np.percentile(errors, 95)  # simple heuristic
        return np.where(errors <= threshold, 1, -1)

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
        ax.set_title("Autoencoder - Anomaly Detection (Training Data)")
        ax.legend()

        outfile = save_dir / f"autoencoder_3d_{dt.datetime.utcnow():%Y%m%dT%H%M%S}.png"
        fig.tight_layout()
        fig.savefig(outfile)
        plt.close(fig)
        return outfile