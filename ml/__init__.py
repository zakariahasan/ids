"""ids.ml package

Convenience re‑exports for anomaly‑detection models and the
:class:`ModelFactory` so callers can do::

    from ids.ml import ModelFactory, IsolationForestModel

This keeps external import lines short while still allowing direct access to
all concrete model classes for advanced use‑cases (e.g. hyper‑parameter tuning
in notebooks).
"""
from __future__ import annotations

from .factory import ModelFactory
from .isolation_forest import IsolationForestModel
from .autoencoder import AutoencoderModel
from .one_class_svm import OneClassSVMModel
from .base import BaseAnomalyModel

__all__: list[str] = [
    "ModelFactory",
    "BaseAnomalyModel",
    "IsolationForestModel",
    "AutoencoderModel",
    "OneClassSVMModel",
]


def list_available_models() -> list[str]:
    """Return a list of model names recognised by :class:`ModelFactory`."""
    return sorted(ModelFactory._models.keys())  # noqa: SLF001