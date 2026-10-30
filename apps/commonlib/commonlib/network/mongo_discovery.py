"""LAN discovery of a MongoDB server, mirroring the MySQL and Ollama scanners.

Only the TCP port is scanned here; MongoDB speaks a binary protocol, so the
candidate is verified by `commonlib.mongo_config.verify_mongo` once the shared
cache layer asks for it.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed

from commonlib.network.discovery import (
    SCAN_TIMEOUT, MAX_WORKERS, get_local_subnets as _detect_subnets,
    scan_port, subnet_hosts,
)
from commonlib.observability import get_logger

logger = get_logger("commonlib.network.mongo_discovery")

DEFAULT_MONGO_PORT = 27017


def get_local_subnets(extra_subnets=()) -> list[str]:
    return _detect_subnets(extra_subnets)


def _scan_port(ip, port, timeout):
    return scan_port(ip, port, timeout)


def _scan_hosts(hosts, port, timeout):
    """Scan a list of hosts on the given port. Returns list of responsive IPs."""
    found = []
    logger.info("mongo.scan_started", hosts=len(hosts), port=port, timeout=timeout)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        fut_map = {ex.submit(_scan_port, h, port, timeout): h for h in hosts}
        for f in as_completed(fut_map):
            if f.result():
                found.append(fut_map[f])
    return found


def discover_mongo_hosts(subnets=None, targets=None, port=None, timeout=None):
    """Scan LAN for hosts with open MongoDB port. Returns list of IPs."""
    port = port or DEFAULT_MONGO_PORT
    timeout = timeout or SCAN_TIMEOUT

    if targets is not None:
        logger.info("mongo.scan_targets", targets=targets, port=port)
        return _scan_hosts(targets, port, timeout)

    if subnets is None:
        subnets = get_local_subnets()

    logger.info("mongo.scan_subnets", subnets=subnets)
    return _scan_hosts(subnet_hosts(subnets, kind="mongo"), port, timeout)
