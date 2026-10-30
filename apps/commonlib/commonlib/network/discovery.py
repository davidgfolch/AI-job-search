"""Shared LAN scanner primitives for MySQL / Mongo / Ollama discovery.

The MySQL and Ollama discovery modules used to carry their own copy of the same
socket scan. This module owns the address probing and subnet detection so the
cache/lock layer (`discovery_cache`) bounds one implementation instead of three.

Subnets scanned: the interfaces of the current machine, plus the usual home
LANs (containers only see the Docker bridge, where an Ollama/MySQL server on
another PC is invisible), plus anything listed in
`COMMONLIB_DISCOVERY_SUBNETS` (comma-separated CIDRs).
"""
import ipaddress
import os
import socket

from commonlib.observability import get_logger

logger = get_logger("commonlib.network.discovery")

SCAN_TIMEOUT = 0.5
MAX_WORKERS = 100
MAX_SCAN_HOSTS = int(os.getenv("COMMONLIB_DISCOVERY_MAX_HOSTS", "0") or 0)
COMMON_LAN_SUBNETS = ("192.168.1.0/24", "192.168.0.0/24")
SUBNETS_ENV = "COMMONLIB_DISCOVERY_SUBNETS"


def get_local_ip():
    """Return the machine's primary LAN IPv4 or None."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except OSError:
        return None
    s.settimeout(2)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return None
    finally:
        s.close()


def configured_subnets() -> tuple[str, ...]:
    """Extra subnets from `COMMONLIB_DISCOVERY_SUBNETS` (CIDR, comma-separated)."""
    return tuple(part.strip() for part in os.getenv(SUBNETS_ENV, "").split(",") if part.strip())


def get_local_subnets(extra_subnets=()) -> list[str]:
    """Detect local LAN subnets: interfaces, common home LANs and configured ones."""
    subnets = []
    local_ip = get_local_ip()
    if local_ip:
        parts = local_ip.split(".")
        subnets.append(f"{parts[0]}.{parts[1]}.{parts[2]}.0/24")
        third = int(parts[2])
        for offset in (-1, 1):
            adj = third + offset
            if 0 <= adj <= 255:
                subnets.append(f"{parts[0]}.{parts[1]}.{adj}.0/24")
    for common in COMMON_LAN_SUBNETS:
        if common not in subnets:
            subnets.append(common)
    for configured in (*configured_subnets(), *extra_subnets):
        if configured not in subnets:
            subnets.append(configured)
    return subnets


def scan_port(ip, port, timeout=SCAN_TIMEOUT):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except OSError:
        return False
    s.settimeout(timeout)
    try:
        return s.connect_ex((ip, port)) == 0
    except Exception:
        return False
    finally:
        s.close()


def subnet_hosts(subnets, kind="lan") -> list[str]:
    """Hosts of every parsable subnet, capped by `COMMONLIB_DISCOVERY_MAX_HOSTS`.

    The scan itself (`commonlib.network.discovery.scan_port`) is driven by each
    service's own scanner, which logs its own literal `<kind>.scan_started`
    event so the console contract stays intact.
    """
    hosts = []
    for subnet_str in subnets:
        try:
            network = ipaddress.IPv4Network(subnet_str, strict=False)
        except Exception:
            continue
        hosts.extend(str(ip) for ip in network.hosts())
        if MAX_SCAN_HOSTS and len(hosts) >= MAX_SCAN_HOSTS:
            logger.warning("discovery.scan_budget_reached", kind=kind, hosts=len(hosts), budget=MAX_SCAN_HOSTS)
            return hosts[:MAX_SCAN_HOSTS]
    return hosts
