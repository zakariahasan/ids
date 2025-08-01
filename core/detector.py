"""Modular detection framework **with alert persistence**."""
from __future__ import annotations

import datetime as dt
from collections import defaultdict
from datetime import datetime
from typing import List

from .alert import EmailAlert
from .db import db  # DatabaseClient singleton

__all__: list[str] = [
    "BaseDetector",
    "SynFloodDetector",
    "DetectorEngine",
]


class BaseDetector:
    """Interface for detectors."""

    def inspect(self, packet):
        """Return list of alert *messages* triggered by *packet*."""


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
        alerts: List[str] = []
        try:
            if packet.tcp.flags == "0x0002":  # SYN flag only
                self.syn_counts[packet.ip.src] += 1
                if self.syn_counts[packet.ip.src] > self.THRESHOLD:
                    alerts.append(f"SYN flood from {packet.ip.src}")
        except AttributeError:
            pass
        return alerts


class DetectorEngine:
    """Aggregates multiple detectors and handles alert side‑effects."""

    def __init__(self, detectors):
        self.detectors = detectors

    def inspect(self, packet):
        all_alerts = []
        for det in self.detectors:
            all_alerts.extend(det.inspect(packet))

        for msg in all_alerts:
            # Persist
            db.insert_alert({
                "ts": dt.datetime.utcnow(),
                "alert_type": msg.split()[0],
                "src_ip": getattr(packet.ip, "src", None),
                "dst_ip": getattr(packet.ip, "dst", None),
                "details": msg,
            })
            # Notify
            EmailAlert.send("IDS", "Intrusion Detected", msg)
        return all_alerts