
"""Abstract base class for **supervised classification** models used in the IDS.

This class mirrors :class:`BaseAnomalyModel` but targets **labelled** datasets
(e.g. URL or packet‑level classes such as *benign*, *phishing*, *malware*).

Concrete subclasses (e.g. *DecisionTreeURLModel*, *RandomForestURLModel*)
must implement at least the following abstract methods:

* :meth:`train` – fit the model on *X* and *y*
* :meth:`predict` – return integer / string labels for unseen *X*
* :meth:`train_and_plot` – helper that trains the model **and** saves a
  diagnostic figure (e.g. confusion‑matrix heat‑map); returns the PNG path.

The optional :meth:`predict_proba` should be overridden if the underlying
algorithm exposes class probabilities (e.g. Random Forest, Logistic
Regression). The default implementation raises *NotImplementedError*.

Sub‑classes are free to expose additional helpers (e.g. *score*,
*feature_importances_*) as needed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np


class BaseClassifierModel(ABC):
    """Blueprint for **supervised** classifier wrappers."""

    # ------------------------------------------------------------------
    # Mandatory API
    # ------------------------------------------------------------------
    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray) -> None:  # pragma: no cover
        """Fit the model on *X* (shape ``[n_samples, n_features]``) and labels *y*."""

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:  # pragma: no cover
        """Return predicted labels for *X*."""

    @abstractmethod
    def train_and_plot(
        self, X: np.ndarray, y: np.ndarray, *, save_dir: Path
    ) -> Path:  # pragma: no cover
        """Train model, create a diagnostic plot, save it into *save_dir* and return the path."""

    # ------------------------------------------------------------------
    # Optional helpers – subclasses may override or rely on these defaults
    # ------------------------------------------------------------------
    def predict_proba(self, X: np.ndarray) -> np.ndarray:  # pragma: no cover
        """Return class probabilities if supported by the underlying algorithm.

        By default this method raises *NotImplementedError*. Algorithms like
        Random Forest or Logistic Regression should override it.
        """
        raise NotImplementedError("predict_proba not implemented for this model")

    # ------------------------------------------------------------------
    # Diagnostics / quality of life
    # ------------------------------------------------------------------
    def __repr__(self) -> str:  # pragma: no cover
        params = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        param_str = ", ".join(f"{k}={v!r}" for k, v in params.items())
        return f"{self.__class__.__name__}({param_str})"
