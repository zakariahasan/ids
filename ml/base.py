"""Abstract base class for anomaly‑detection models used in IDS."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np

class BaseAnomalyModel(ABC):
    """Blueprint for all anomaly‑detection wrappers.

    Concrete subclasses (e.g. *IsolationForestModel*, *AutoencoderModel*) must
    implement at least the following abstract methods:

    * :meth:`train` – fit the model on a normal‑traffic dataset ``X``
    * :meth:`predict` – label new samples (1 =inlier, ‑1 =outlier)
    * :meth:`train_and_plot` – helper that trains and saves a diagnostic figure;
      returns a :class:`pathlib.Path` to the saved PNG so the UI can embed it.
    * ``score_samples`` is optional but recommended if the algorithm provides a
      continuous anomaly score.
    """

    # ------------------------------------------------------------------
    # Mandatory API
    # ------------------------------------------------------------------
    @abstractmethod
    def train(self, X: np.ndarray) -> None:  # pragma: no cover
        """Fit the model on *X* (array‑like of shape ``[n_samples, n_features]``)."""

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:  # pragma: no cover
        """Return an array of labels (1 =inlier, ‑1 =outlier)."""

    @abstractmethod
    def train_and_plot(self, X: np.ndarray, *, save_dir: Path) -> Path:  # pragma: no cover
        """Train model, create a diagnostic plot, save it into *save_dir* and return the path."""

    # ------------------------------------------------------------------
    # Optional helpers – subclasses may override or rely on these defaults
    # ------------------------------------------------------------------
    def score_samples(self, X: np.ndarray) -> np.ndarray:  # pragma: no cover
        """Return raw anomaly scores if the underlying algorithm supports it.

        By default this method raises *NotImplementedError*. Algorithms such as
        Isolation Forest or One‑Class SVM should override it to expose their
        native scoring (decision function, reconstruction error, etc.).
        """
        raise NotImplementedError("score_samples not implemented for this model")

    # ------------------------------------------------------------------
    # Diagnostics / quality of life
    # ------------------------------------------------------------------
    def __repr__(self) -> str:  # pragma: no cover
        params = {
            k: v for k, v in self.__dict__.items() if not k.startswith("_")
        }
        param_str = ", ".join(f"{k}={v!r}" for k, v in params.items())
        return f"{self.__class__.__name__}({param_str})"