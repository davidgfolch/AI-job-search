"""LAN discovery of an Ollama server, mirroring `mysql_discovery.py`.

The scanner is gated by the caller: `ollama_probe` only runs it when
`COMMONLIB_OLLAMA_DISCOVERY` is enabled (default True), and every result is
cached in `discovery_cache` so a worker does not rescan the LAN per job or per
restart.

`COMMONLIB_DISCOVERY_SUBNETS` (shared with MySQL/Mongo) and the legacy
`COMMONLIB_OLLAMA_DISCOVERY_SUBNETS` (comma-separated CIDRs) add subnets to
scan. This is useful when the scanner runs inside a Docker container, where
auto-detection only sees the Docker network and not the host LAN where an
Ollama server on another PC may live.
"""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from commonlib.network.discovery import (
    SCAN_TIMEOUT, MAX_WORKERS, get_local_ip as get_local_ip, get_local_subnets as _detect_subnets,
    scan_port, subnet_hosts,
)
from commonlib.observability import get_logger

logger = get_logger("commonlib.network.ollama_discovery")

DEFAULT_OLLAMA_PORT = 11434
SPEC_LOCAL = ("local", "localhost", "127.0.0.1")
SPEC_AUTO = ("auto", "discover")
OLLAMA_DISCOVERY_SUBNETS = tuple(
    part.strip() for part in os.getenv("COMMONLIB_OLLAMA_DISCOVERY_SUBNETS", "").split(",") if part.strip()
)


def get_local_subnets(extra_subnets=()) -> list[str]:
    return _detect_subnets((*OLLAMA_DISCOVERY_SUBNETS, *extra_subnets))


def _scan_port(ip, port, timeout):
    return scan_port(ip, port, timeout)


def _scan_hosts(hosts, port, timeout):
    """Scan a list of hosts on the given port. Returns list of responsive IPs."""
    found = []
    logger.info("ollama.scan_started", hosts=len(hosts), port=port, timeout=timeout)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        fut_map = {ex.submit(_scan_port, h, port, timeout): h for h in hosts}
        for f in as_completed(fut_map):
            if f.result():
                found.append(fut_map[f])
    return found


def discover_ollama_hosts(subnets=None, targets=None, port=None, timeout=None):
    """Scan LAN for hosts with open Ollama port. Returns list of IPs.

    Args:
        subnets: List of CIDR subnets to scan (e.g. ['192.168.1.0/24']).
                 Ignored if targets is provided.
        targets: Specific list of IPs to scan.
        port: Ollama port (default 11434).
        timeout: Per-host scan timeout in seconds (default 0.5).
    """
    port = port or DEFAULT_OLLAMA_PORT
    timeout = timeout or SCAN_TIMEOUT

    if targets is not None:
        logger.info("ollama.scan_targets", targets=targets, port=port)
        return _scan_hosts(targets, port, timeout)

    if subnets is None:
        subnets = get_local_subnets()

    logger.info("ollama.scan_subnets", subnets=subnets)
    return _scan_hosts(subnet_hosts(subnets, kind="ollama"), port, timeout)
