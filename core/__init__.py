"""ids.core package

Aggregates the core runtime components of Next Gen‑IDS so callers can do::

    from ids.core import PacketSniffer, DetectorEngine, SynFloodDetector, run_sniffer

This file re‑exports the most commonly used classes and utilities, providing a
single import surface while *still* allowing more granular imports from the
underlying modules when necessary.
"""
from __future__ import annotations

from . import config
from .alert import EmailAlert
from .capture import PacketSniffer, run_sniffer
from .detector import DetectorEngine, SynFloodDetector

__all__: list[str] = [
    # sub‑modules
    "config",
    # alerting
    "EmailAlert",
    # detection / capture
    "DetectorEngine",
    "SynFloodDetector",
    "PacketSniffer",
    "run_sniffer",
]