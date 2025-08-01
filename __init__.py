"""Top‑level package for IDS."""

from importlib.metadata import version
__version__ = "0.1.0"

# Re‑export core factories for convenience
from .ml.factory import ModelFactory