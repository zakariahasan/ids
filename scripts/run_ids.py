"""Command‑line entry point for running the live IDS sniffer.

*Windows‑friendly fix*: the previous version attempted to register POSIX
signal handlers via :py:meth:`asyncio.loop.add_signal_handler`, which raises
``NotImplementedError`` on the default Windows event loop. We now:

* Register SIGINT/SIGTERM handlers **only** on non‑Windows platforms.
* Always rely on ``KeyboardInterrupt`` (Ctrl‑C) to stop gracefully.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import signal
import sys
from typing import Sequence

from ids.core import DetectorEngine, PacketSniffer, SynFloodDetector, config

# ---------------------------------------------------------------------------
# Helper factory
# ---------------------------------------------------------------------------

def _build_engine() -> DetectorEngine:
    """Return a DetectorEngine instance with configured detectors."""
    return DetectorEngine(detectors=[SynFloodDetector()])


def _run(interface: str) -> None:
    """Synchronous wrapper to run the packet sniffer."""
    sniffer = PacketSniffer(interface, _build_engine())
    sniffer.run()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Next Gen‑IDS packet sniffer")
    parser.add_argument(
        "-i",
        "--interface",
        default=config.INTERFACE,
        help="Network interface to monitor (default taken from ids.core.config)",
    )
    return parser.parse_args(argv)


def _setup_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    """Attach SIGINT/SIGTERM handlers where supported (POSIX)."""
    if os.name != "nt":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, loop.stop)
    # On Windows, KeyboardInterrupt will suffice.


def main(argv: Sequence[str] | None = None) -> None:  # pragma: no cover
    args = _parse_args(argv)

    try:
        print("[INFO] IDS runing..")

        _run(args.interface)
    except KeyboardInterrupt:
        print("[INFO] Ctrl‑C pressed — shutting down IDS.")
    finally:
        print("[INFO] IDS stopped.")


if __name__ == "__main__":
    main()
