"""LAN discovery of an Ollama server, mirroring `mysql_discovery.py`.

The scanner is gated by the caller: `ollama_client` only runs it when
`COMMONLIB_OLLAMA_DISCOVERY` is enabled (default True).

`COMMONLIB_OLLAMA_DISCOVERY_SUBNETS` (comma-separated CIDRs) adds extra
subnets to scan. This is useful when the scanner runs inside a Docker
container, where auto-detection only sees the Docker network and not the
host LAN where an Ollama server on another PC may live.
"""
import ipaddress
import os
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

from commonlib.observability import get_logger

logger = get_logger("commonlib.network.ollama_discovery")

DEFAULT_OLLAMA_PORT = 11434
SCAN_TIMEOUT = 0.5
MAX_WORKERS = 100
SPEC_LOCAL = ('local', 'localhost', '127.0.0.1')
SPEC_AUTO = ('auto', 'discover')
OLLAMA_DISCOVERY_SUBNETS = tuple(
    part.strip() for part in os.getenv("COMMONLIB_OLLAMA_DISCOVERY_SUBNETS", "").split(",") if part.strip()
)


def get_local_ip():
    """Return the machine's primary LAN IPv4 or None."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return None
    finally:
        s.close()


def get_local_subnets():
    """Detect local LAN subnets by finding the machine's IP via UDP connect.

    From inside a Docker container this only sees the Docker bridge network,
    so common LAN /24s are appended so Ollama on another machine in the host LAN
    is discovered automatically (no env var required). Extra subnets can be added
    with ``COMMONLIB_OLLAMA_DISCOVERY_SUBNETS``.
    """
    subnets = []
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    try:
        s.connect(("8.8.8.8", 80))
        parts = s.getsockname()[0].split(".")
        subnets.append(f"{parts[0]}.{parts[1]}.{parts[2]}.0/24")
        third = int(parts[2])
        for offset in (-1, 1):
            adj = third + offset
            if 0 <= adj <= 255:
                subnets.append(f"{parts[0]}.{parts[1]}.{adj}.0/24")
    except Exception:
        pass
    finally:
        s.close()
    # Common LAN subnets so discovery works automatically from inside Docker
    # containers, where auto-detection only sees the Docker bridge network.
    for common in ("192.168.1.0/24", "192.168.0.0/24"):
        if common not in subnets:
            subnets.append(common)
    # Extra subnets (e.g. a different host LAN when scanning from Docker).
    subnets.extend(OLLAMA_DISCOVERY_SUBNETS)
    seen = set()
    unique = []
    for subnet in subnets:
        if subnet not in seen:
            seen.add(subnet)
            unique.append(subnet)
    return unique


def _scan_port(ip, port, timeout):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        return s.connect_ex((ip, port)) == 0
    except Exception:
        return False
    finally:
        s.close()


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

    found = []
    logger.info("ollama.scan_subnets", subnets=subnets)
    for subnet_str in subnets:
        try:
            network = ipaddress.IPv4Network(subnet_str, strict=False)
        except Exception:
            continue
        hosts = [str(ip) for ip in network.hosts()]
        found.extend(_scan_hosts(hosts, port, timeout))
    return found
