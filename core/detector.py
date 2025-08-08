"""
ids.core.detector
=================
Modular detection framework.

Highlights
----------
* Keeps `SynFloodDetector` exactly as before.
* Adds `ModelBasedURLDetector` + `ModelBasedBehaviourDetector`.
* Persists alerts with `model_name` for the new /alerts/ dashboard.
* **Fixes circular import** by lazy-importing ModelFactory only when
  needed (no top-level `from ids.ml.factory ...`).
"""

from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List, Sequence, Tuple, Union

import pyshark

from ids.core import config
from .alert import EmailAlert
from .db import db  # DatabaseClient singleton

if TYPE_CHECKING:  # keeps mypy / IDE happy but avoids runtime import
    from ids.ml.factory import ModelFactory  # noqa: F401

__all__ = [
    "BaseDetector",
    "SynFloodDetector",
    "ModelBasedURLDetector",
    "ModelBasedBehaviourDetector",
    "DetectorEngine",
]

# --------------------------------------------------------------------- #
# A tiny helper to avoid circular imports
# --------------------------------------------------------------------- #
def _create_model(name: str):
    """Lazy import to break core ↔ ml cycle."""
    from ids.ml.factory import ModelFactory

    return ModelFactory.create(name)


# --------------------------------------------------------------------- #
# Helper to discover which model is currently selected by analyst
# --------------------------------------------------------------------- #
_MODEL_CHOICE_FILE = Path(config.BASE_DIR) / "current_model.txt"


def _current_model() -> str:
    if _MODEL_CHOICE_FILE.exists():
        return _MODEL_CHOICE_FILE.read_text().strip()
    return "DecisionTree"  # default


# --------------------------------------------------------------------- #
# Base class
# --------------------------------------------------------------------- #
class BaseDetector:
    """Interface for detectors.

    `inspect(packet)` should yield **either**

    * str – alert message (engine infers model from detector class), or
    * tuple(str, str) – (message, model_name)
    """

    def inspect(self, packet) -> List[Union[str, Tuple[str, str]]]:
        raise NotImplementedError


# --------------------------------------------------------------------- #
# Classic SYN-Flood detector (unchanged)
# --------------------------------------------------------------------- #
class SynFloodDetector(BaseDetector):
    WINDOW_SEC = 1
    THRESHOLD = 5

    def __init__(self):
        self.syn_counts = defaultdict(int)
        self.window_start = datetime.utcnow()

    def _rotate_window(self):
        if (datetime.utcnow() - self.window_start).total_seconds() >= self.WINDOW_SEC:
            self.syn_counts.clear()
            self.window_start = datetime.utcnow()

    def inspect(self, packet):
        self._rotate_window()
        alerts: List[Tuple[str, str]] = []
        try:
            if packet.tcp.flags == "0x0002":  # SYN flag only
                self.syn_counts[packet.ip.src] += 1
                if self.syn_counts[packet.ip.src] > self.THRESHOLD:
                    alerts.append((f"SYN flood from {packet.ip.src}", "SynFlood"))
        except AttributeError:
            pass
        return alerts


# --------------------------------------------------------------------- #
# URL model-based detector (supervised)
# --------------------------------------------------------------------- #
_URL_RE = re.compile(r"^https?://", re.I)


class ModelBasedURLDetector(BaseDetector):
    """Uses a trained URL classifier to flag phishing/defacement/etc."""

    def __init__(self):
        self.model_name = _current_model()
        self.model = _create_model(self.model_name)

    def _maybe_reload(self):
        new_name = _current_model()
        if new_name != self.model_name:
            self.model_name = new_name
            self.model = _create_model(new_name)

    @staticmethod
    def _extract_full_url(packet) -> str | None:
        try:
            # HTTP
            if hasattr(packet, "http"):
                http = packet.http
                host = getattr(http, "host", None)
                uri = getattr(http, "request_full_uri", None) or getattr(
                    http, "request_uri", None
                )
                if host and uri:
                    return (
                        uri
                        if _URL_RE.match(uri)
                        else f"http://{host}{uri}"
                    )
                if host:
                    return f"http://{host}"

            # HTTPS (SNI)
            elif hasattr(packet, "tls"):
                sni = getattr(packet.tls, "handshake_extensions_server_name", None)
                if sni:
                    return f"https://{sni}"
        except AttributeError:
            pass
        return None

    def inspect(self, packet):
        self._maybe_reload()
        url = self._extract_full_url(packet)
        if not url:
            return []

        try:
            pred = self.model.predict([url])[0]
        except Exception:
            return []

        if str(pred).lower() != "benign":
            return [(f"{pred} URL detected: {url}", self.model_name)]
        return []


# --------------------------------------------------------------------- #
# Behaviour-based anomaly detector (unsupervised)
# --------------------------------------------------------------------- #
class ModelBasedBehaviourDetector(BaseDetector):
    """Detects abnormal packet features via an unsupervised model."""

    def __init__(self):
        self.model_name = _current_model()
        self.model = _create_model(self.model_name)

    def _maybe_reload(self):
        new_name = _current_model()
        if new_name != self.model_name:
            self.model_name = new_name
            self.model = _create_model(new_name)

    @staticmethod
    def _to_vector(packet) -> list[float]:
        return [float(getattr(packet, "length", 0) or 0)]

    def inspect(self, packet):
        self._maybe_reload()
        vec = [self._to_vector(packet)]
        try:
            score = self.model.predict(vec)[0]
        except Exception:
            return []

        if score == -1 or str(score).lower() in {"anomaly", "attack"}:
            return [
                (
                    f"Anomalous behaviour detected (model={self.model_name})",
                    self.model_name,
                )
            ]
        return []


# --------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------- #
class DetectorEngine:
    """Aggregates detectors and handles alert side-effects."""

    def __init__(self, detectors: Sequence[BaseDetector]):
        self.detectors = list(detectors)

    def inspect(self, packet):
        collected: List[Tuple[str, str]] = []

        for det in self.detectors:
            for outcome in det.inspect(packet):
                if isinstance(outcome, tuple):
                    collected.append(outcome)
                else:
                    collected.append((outcome, det.__class__.__name__))

        for msg, model_used in collected:
            # Persist to DB
            db.insert_alert(
                {
                    "ts": dt.datetime.utcnow(),
                    "alert_type": msg.split()[0],
                    "src_ip": getattr(packet.ip, "src", None),
                    "dst_ip": getattr(packet.ip, "dst", None),
                    "details": msg,
                    "model_name": model_used,
                }
            )
            # Notify (email / webhook / etc.)
            EmailAlert.send("IDS", "Intrusion Detected", msg)

        return [m for m, _ in collected]
