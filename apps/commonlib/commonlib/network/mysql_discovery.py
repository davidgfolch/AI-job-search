"""LAN discovery of a MySQL server.

The scanner is gated by the caller (`connection_manager.DB_DISCOVERY_ENABLED`),
and every result is cached in `discovery_cache` so a cold start scans once
instead of once per container and per retry.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed

from commonlib.network.discovery import (
    SCAN_TIMEOUT, MAX_WORKERS, get_local_ip, get_local_subnets as _detect_subnets,
    scan_port, subnet_hosts,
)
from commonlib.network.discovery_cache import cached_discover
from commonlib.observability import get_logger

logger = get_logger("commonlib.network.mysql_discovery")

DEFAULT_MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'rootPass'
MYSQL_DATABASE = 'jobs'
SPEC_LOCAL = ('local', 'localhost', '127.0.0.1')
SPEC_AUTO = ('auto', 'discover')


def get_local_subnets(extra_subnets=()) -> list[str]:
    return _detect_subnets(extra_subnets)


def _scan_port(ip, port, timeout):
    return scan_port(ip, port, timeout)


def _scan_hosts(hosts, port, timeout):
    """Scan a list of hosts on the given port. Returns list of responsive IPs."""
    found = []
    logger.info("mysql.scan_started", hosts=len(hosts), port=port, timeout=timeout)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        fut_map = {ex.submit(_scan_port, h, port, timeout): h for h in hosts}
        for f in as_completed(fut_map):
            if f.result():
                found.append(fut_map[f])
    return found


def discover_mysql_hosts(subnets=None, targets=None, port=None, timeout=None):
    """Scan LAN for hosts with open MySQL port. Returns list of IPs.

    Args:
        subnets: List of CIDR subnets to scan (e.g. ['192.168.1.0/24']).
                 Ignored if targets is provided.
        targets: Specific list of IPs to scan.
        port: MySQL port (default 3306).
        timeout: Per-host scan timeout in seconds (default 0.5).
    """
    port = port or DEFAULT_MYSQL_PORT
    timeout = timeout or SCAN_TIMEOUT

    if targets is not None:
        logger.info("mysql.scan_targets", targets=targets, port=port)
        return _scan_hosts(targets, port, timeout)

    if subnets is None:
        subnets = get_local_subnets()

    logger.info("mysql.scan_subnets", subnets=subnets)
    return _scan_hosts(subnet_hosts(subnets, kind="mysql"), port, timeout)


def verify_mysql(host, port=None, user=None, password=None, database=None):
    """Verify host is our MySQL — connect and check the database exists."""
    import mysql.connector
    port = port or DEFAULT_MYSQL_PORT
    user = user or MYSQL_USER
    password = password or MYSQL_PASSWORD
    database = database or MYSQL_DATABASE
    try:
        conn = mysql.connector.connect(
            host=host, port=port, user=user, password=password,
            database=database, connect_timeout=3
        )
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s",
            (database,)
        )
        exists = cursor.fetchone()[0] > 0
        cursor.close()
        conn.close()
        return exists
    except Exception:
        return False


def auto_discover_host():
    """Auto-discover MySQL host on LAN, using and refreshing the shared cache."""
    try:
        return cached_discover("mysql", verify=verify_mysql, scan=discover_mysql_hosts, log=logger)
    except Exception as e:
        logger.warning("mysql.discovery_failed", error=str(e))
        return None


def resolve_mysql_host(spec='auto'):
    """Resolve a host spec to a reachable MySQL host IP.

    - 'local' | 'localhost' | '127.0.0.1' -> 127.0.0.1 (assumed, no probe)
    - 'auto' | 'discover' -> cached LAN discovery, first verified host excluding local
    - otherwise -> the given IP, verified as a MySQL host

    Raises ConnectionError when nothing can be resolved.
    """
    spec = (spec or 'auto').strip().lower()
    if spec in SPEC_LOCAL:
        return '127.0.0.1'
    if spec in SPEC_AUTO:
        local = get_local_ip()
        host = cached_discover("mysql", verify=verify_mysql, scan=discover_mysql_hosts, log=logger, tried={local})
        if host:
            return host
        raise ConnectionError('Auto-discovery found no reachable MySQL host on the LAN')
    if verify_mysql(spec):
        return spec
    raise ConnectionError(f"MySQL host '{spec}' is not reachable or has no '{MYSQL_DATABASE}' database")
