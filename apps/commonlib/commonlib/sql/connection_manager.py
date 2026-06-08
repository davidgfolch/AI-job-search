import ipaddress
import os
import mysql.connector as mysqlConnector
from mysql.connector import MySQLConnection

from commonlib.terminalColor import green

DEBUG = False

DEFAULT_MYSQL_PORT = 3306
SMALL_RANGE_THRESHOLD = 10

_pool_initialized = False


def _parse_ip_range(range_str: str) -> list[str]:
    """Parse an IP range (start-end) into a list of IPs.
    Supports: 192.168.0.10-192.168.0.250, 192.168.0.10-250."""
    start_str, end_str = (x.strip() for x in range_str.split('-', 1))
    start_ip = ipaddress.IPv4Address(start_str)
    end_parts = end_str.split('.')
    if len(end_parts) < 4:
        start_parts = start_str.split('.')
        if len(end_parts) == 1:
            padded = start_parts[:3] + end_parts
        elif len(end_parts) == 2:
            padded = start_parts[:2] + end_parts
        elif len(end_parts) == 3:
            if end_parts[:2] == start_parts[:2]:
                padded = start_parts[:3] + [end_parts[2]]
            else:
                padded = [start_parts[0]] + end_parts
        end_str = '.'.join(padded)
    end_ip = ipaddress.IPv4Address(end_str)
    start_int = int(start_ip)
    end_int = int(end_ip)
    if end_int < start_int:
        raise ValueError(f"Range end {end_str} < start {start_str}")
    return [str(ipaddress.IPv4Address(i)) for i in range(start_int, end_int + 1)]


def _parse_host_targets(raw: str) -> list[str]:
    """Parse COMMONLIB_DB_HOST into a list of IPs.
    Supports: single IP, CIDR (192.168.1.0/24), range (10-250),
    comma-separated combinations."""
    targets = []
    for part in raw.split(','):
        part = part.strip()
        if not part:
            continue
        if '/' in part:
            try:
                network = ipaddress.IPv4Network(part, strict=False)
                targets.extend(str(ip) for ip in network.hosts())
            except ValueError:
                try:
                    targets.extend(_parse_ip_range(part.replace('/', '-', 1)))
                except Exception:
                    targets.append(part)
        elif '-' in part:
            try:
                targets.extend(_parse_ip_range(part))
            except Exception:
                targets.append(part)
        else:
            targets.append(part)
    return targets


def _probe_mysql(host: str, e2e_tests: bool = False, timeout: int = 3):
    """Test if MySQL is reachable at host. Raises on failure."""
    conn = mysqlConnector.connect(
        host=host, user='root', password='rootPass',
        database=None if e2e_tests else 'jobs',
        connect_timeout=timeout,
    )
    conn.close()


def _try_targets(targets: list[str], e2e_tests: bool) -> str | None:
    """Try to find a reachable MySQL host in targets. Returns host or None."""
    if len(targets) <= SMALL_RANGE_THRESHOLD:
        for host in targets:
            try:
                _probe_mysql(host, e2e_tests)
                return host
            except Exception:
                pass
    else:
        from commonlib.network.mysql_discovery import discover_mysql_hosts, verify_mysql
        open_hosts = discover_mysql_hosts(targets=targets)
        if open_hosts:
            open_set = set(open_hosts)
            for host in targets:
                if host in open_set and verify_mysql(host):
                    return host
    return None


def _resolve_db_host(e2e_tests: bool = False) -> str:
    """Resolve MySQL host — try configured targets, fall back to LAN discovery."""
    raw = os.getenv('COMMONLIB_DB_HOST', '').strip()

    resolved = None
    if raw:
        groups = [g.strip() for g in raw.split(',') if g.strip()]
        for group_raw in groups:
            targets = _parse_host_targets(group_raw)
            resolved = _try_targets(targets, e2e_tests)
            if resolved:
                break
    else:
        resolved = _try_targets(['127.0.0.1'], e2e_tests)

    if not resolved:
        from commonlib.network.mysql_discovery import auto_discover_host
        resolved = auto_discover_host()

    if resolved:
        print(green(f"MySQL at {resolved}"), flush=True)
        return resolved

    raise ConnectionError(
        "Could not connect to MySQL via configured hosts or LAN discovery"
    )


def _init_pool(e2e_tests: bool = False):
    """Initialize the connection pool once."""
    global _pool_initialized
    if _pool_initialized:
        return
    db_host = _resolve_db_host(e2e_tests)
    mysqlConnector.connect(
        host=db_host,
        user='root',
        password='rootPass',
        database=None if e2e_tests else 'jobs',
        pool_name='jobsPool',
        pool_size=20,
    )
    _pool_initialized = True


def get_connection(e2e_tests: bool = False) -> MySQLConnection:
    """
    Get a MySQL connection from the pool.
    Caller MUST close the connection to return it to the pool.

    Args:
        e2e_tests: If True, initializes pool without database (for E2E test setup)

    Returns:
        MySQL connection instance from pool
    """
    _init_pool(e2e_tests)
    conn = mysqlConnector.connect(pool_name='jobsPool')
    if DEBUG:
        print(conn.__repr__())
    return conn


def getConnection(e2eTests: bool = False) -> MySQLConnection:
    """Backward compatible wrapper for get_connection."""
    return get_connection(e2e_tests=e2eTests)
