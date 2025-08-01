"""Test suite package for Next Gen‑IDS.

This file provides common fixtures/utility helpers that can be imported by all
individual test modules. Keeping them here avoids circular imports and makes it
simple to share objects (e.g., an in‑memory database, dummy packets, etc.).

If you don't need shared fixtures yet, this file can remain empty — but adding
it ensures *tests* is a proper Python package so pytest can discover the test
modules even when the project is installed as a wheel.
"""
from __future__ import annotations

import types
from pathlib import Path
from typing import Iterator

import pytest

from ids.core.detector import SynFloodDetector

# ---------------------------------------------------------------------------
# Pytest fixtures (extend as needed)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return Path object pointing to the project root directory."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture()
def dummy_syn_packet() -> types.SimpleNamespace:
    """Return a simple object that mimics a TCP SYN packet for detector tests."""
    return types.SimpleNamespace(
        ip=types.SimpleNamespace(src="10.0.0.99"),
        tcp=types.SimpleNamespace(flags="0x0002"),
    )


@pytest.fixture()
def primed_syn_detector() -> SynFloodDetector:
    """Return a SynFloodDetector instance with an already‑primed window."""
    return SynFloodDetector()