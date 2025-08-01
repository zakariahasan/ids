"""
ids.core.capture
================
Sniffs packets with PyShark, writes raw rows into **packets**, updates
per-host counters in memory, periodically flushes those statistics into
**host_stats**, and feeds every packet to the DetectorEngine.

* Non-IP frames are ignored gracefully.
* Uses a lazy import for the DB singleton to avoid circular imports.
"""

from __future__ import annotations

import datetime as dt
import importlib
import time
from collections import defaultdict
from ipaddress import ip_address
from typing import Optional

import pyshark

from . import config
from .detector import DetectorEngine, SynFloodDetector

# --------------------------------------------------------------------------- #
# Globals                                                                      #
# --------------------------------------------------------------------------- #

STATS_INTERVAL = 60  # seconds to aggregate before flush

host_counters = defaultdict(
    lambda: {
        "total": 0,       # packets total (in+out)
        "in": 0,          # dst-side
        "out": 0,         # src-side
        "src_ips": set(),  # src IPs seen
        "dst_ports": set(),  # ports hit
        "total_len": 0,
    }
)
last_stats_flush = time.time()

# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _lazy_db():
    """Import `db` lazily to break circular-import during package init."""
    return importlib.import_module("ids.core.db").db  # type: ignore[attr-defined]


class PacketSniffer:
    """
    Capture packets, persist raw rows, update host stats, flush periodically,
    and pass packets to the DetectorEngine.
    """

    def __init__(self, interface: str, detector: DetectorEngine):
        self.interface = interface
        self.detector = detector
        self._db = None  # bound lazily

    # --------------------------- Packet helpers --------------------------- #
    def _extract_fields(self, packet) -> dict[str, Optional[str]]:
        """Return minimal dict for DB insert. Tolerate non-IP frames."""
        try:
            proto = packet.transport_layer or packet.highest_layer
        except AttributeError:
            proto = "UNKNOWN"

        # IPv4 / IPv6?
        src_ip = dst_ip = None
        try:
            src_ip = packet.ip.src  # type: ignore[attr-defined]
            dst_ip = packet.ip.dst  # type: ignore[attr-defined]
        except AttributeError:
            pass  # Non-IP frame (ARP, etc.)

        src_port = dst_port = None
        if proto in ("TCP", "UDP"):
            layer = getattr(packet, proto.lower(), None)
            if layer:
                src_port = getattr(layer, "srcport", None)
                dst_port = getattr(layer, "dstport", None)

        length = int(getattr(packet, "length", 0) or 0)
        tcp_flags = getattr(getattr(packet, "tcp", None), "flags", None)

        return {
            "ts": packet.sniff_time.replace(tzinfo=None),
            "src_ip": src_ip,
            "src_port": int(src_port) if src_port else None,
            "dst_ip": dst_ip,
            "dst_port": int(dst_port) if dst_port else None,
            "protocol": proto,
            "length": length,
            "tcp_flags": str(tcp_flags) if tcp_flags else None,
        }

    def _persist_packet(self, fields: dict[str, Optional[str]]) -> None:
        if not self._db:
            self._db = _lazy_db()

        # Skip if not an IP packet
        if not fields["src_ip"] or not fields["dst_ip"]:
            return
        try:
            ip_address(fields["src_ip"])
            ip_address(fields["dst_ip"])
        except ValueError:
            return

        self._db.insert_packet(fields)  # type: ignore[arg-type]

    # --------------------------- Host counters --------------------------- #
    def _update_stats(self, fields: dict[str, Optional[str]]) -> None:
        src = fields["src_ip"]
        dst = fields["dst_ip"]
        if not src or not dst:
            return

        length = fields["length"] or 0
        dst_port = fields["dst_port"]

        # Source host
        hc_src = host_counters[src]
        hc_src["total"] += 1
        hc_src["out"] += 1
        hc_src["src_ips"].add(src)
        if dst_port:
            hc_src["dst_ports"].add(dst_port)
        hc_src["total_len"] += length

        # Destination host
        hc_dst = host_counters[dst]
        hc_dst["total"] += 1
        hc_dst["in"] += 1
        hc_dst["src_ips"].add(src)
        if dst_port:
            hc_dst["dst_ports"].add(dst_port)
        hc_dst["total_len"] += length

    # --------------------------- Stats flush ----------------------------- #
    def _flush_host_stats(self) -> None:
        if not self._db or not host_counters:
            return

        now = dt.datetime.utcnow()
        interval_start = now.replace(second=0, microsecond=0) - dt.timedelta(
            seconds=STATS_INTERVAL
        )
        interval_end = interval_start + dt.timedelta(seconds=STATS_INTERVAL)

        for host, counters in list(host_counters.items()):
            self._db.insert_host_stats(
                {
                    "interval_start": interval_start,
                    "interval_end": interval_end,
                    "host_ip": host,
                    "total_packets": counters["total"],
                    "total_packets_size": counters["total_len"],
                    "incoming_packets": counters["in"],
                    "outgoing_packets": counters["out"],
                    "unique_src_ips": len(counters["src_ips"]),
                    "unique_dst_ports": len(counters["dst_ports"]),
                }
            )

        host_counters.clear()

    # --------------------------- Main loop ------------------------------ #
    def run(self) -> None:
        global last_stats_flush

        capture = pyshark.LiveCapture(interface=self.interface)

        for packet in capture.sniff_continuously():
            fields = self._extract_fields(packet)
            self._persist_packet(fields)
            self._update_stats(fields)
            self.detector.inspect(packet)

            # Periodic stats flush
            if time.time() - last_stats_flush >= STATS_INTERVAL:
                self._flush_host_stats()
                last_stats_flush = time.time()


# ----------------------------------------------------------------------------
# Convenience helper (used by scripts.run_ids)
# ----------------------------------------------------------------------------
def run_sniffer() -> None:  # pragma: no cover
    engine = DetectorEngine(detectors=[SynFloodDetector()])
    PacketSniffer(config.INTERFACE, engine).run()
