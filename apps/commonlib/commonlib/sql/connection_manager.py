import os
import queue
import threading
import time
import mysql.connector as mysqlConnector
from mysql.connector import MySQLConnection

from commonlib.environmentUtil import getEnv
from commonlib.observability import get_logger
from commonlib.sql.connection_manager_parse import _parse_host_targets as _parse_host_targets, _parse_ip_range as _parse_ip_range
from commonlib.sql.db_hosts import (
    DB_AUTO_SPECS as DB_AUTO_SPECS, DB_CANDIDATE_HOSTS as DB_CANDIDATE_HOSTS, db_candidate_hosts as db_candidate_hosts,
)
from commonlib.sql.db_wait import wait_for_db as wait_for_db

logger = get_logger("commonlib.sql.connection_manager")

DEBUG = False

DEFAULT_DB_NAME = 'jobs'
DEFAULT_MYSQL_PORT = 3306
SMALL_RANGE_THRESHOLD = 10
POOL_GET_RETRIES = int(os.getenv('COMMONLIB_DB_POOL_RETRIES', '3'))
POOL_GET_DELAY = float(os.getenv('COMMONLIB_DB_POOL_RETRY_DELAY', '0.1'))
DB_DISCOVERY_ENABLED = os.getenv('COMMONLIB_DB_DISCOVERY', 'True').strip().lower() not in ('false', '0', 'no')


_pool_initialized = False
_pool_lock = threading.Lock()


def get_db_name() -> str:
    """Database the runtime connects to (COMMONLIB_DB_NAME, default 'jobs').

    Lets a second checkout work on its own schema on the same MySQL server
    without touching the live `jobs` database.
    """
    return getEnv('COMMONLIB_DB_NAME', DEFAULT_DB_NAME) or DEFAULT_DB_NAME


def _probe_mysql(host: str, e2e_tests: bool = False, timeout: int = 3):
    """Test if MySQL is reachable at host. Raises on failure."""
    conn = mysqlConnector.connect(
        host=host, user='root', password='rootPass',
        database=None if e2e_tests else get_db_name(),
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
    """Resolve MySQL host — try the candidate chain, fall back to (cached) LAN discovery."""
    raw = os.getenv('COMMONLIB_DB_HOST', '').strip()
    resolved = None if raw.lower() in DB_AUTO_SPECS else _try_targets(list(db_candidate_hosts(raw)), e2e_tests)

    if not resolved and DB_DISCOVERY_ENABLED:
        from commonlib.network.mysql_discovery import auto_discover_host
        resolved = auto_discover_host()

    if resolved:
        logger.info("db.host_resolved", host=resolved)
        return resolved

    reason = "Could not connect to MySQL via configured hosts or LAN discovery"
    if not DB_DISCOVERY_ENABLED:
        reason = "Could not connect to MySQL via configured hosts (COMMONLIB_DB_DISCOVERY=False)"
    raise ConnectionError(reason)


def _init_pool(e2e_tests: bool = False):
    """Initialize the connection pool once (thread-safe)."""
    global _pool_initialized
    if _pool_initialized:
        return
    with _pool_lock:
        if _pool_initialized:
            return
        pool_size = int(os.getenv('COMMONLIB_DB_POOL_SIZE', '5'))
        db_host = _resolve_db_host(e2e_tests)
        conn = mysqlConnector.connect(
            host=db_host,
            user='root',
            password='rootPass',
            database=None if e2e_tests else get_db_name(),
            pool_name='jobsPool',
            pool_size=pool_size,
            pool_reset_session=True,
        )
        conn.close()
        _pool_initialized = True


def get_connection(e2e_tests: bool = False) -> MySQLConnection:
    """
    Get a MySQL connection from the pool.
    Caller MUST close the connection to return it to the pool.

    Retries with backoff when the pool is temporarily exhausted.

    Args:
        e2e_tests: If True, initializes pool without database (for E2E test setup)

    Returns:
        MySQL connection instance from pool
    """
    _init_pool(e2e_tests)
    for attempt in range(POOL_GET_RETRIES):
        try:
            conn = mysqlConnector.connect(pool_name='jobsPool')
            if DEBUG:
                logger.debug("db.connection_opened", conn=repr(conn))
            return conn
        except (queue.Empty, mysqlConnector.errors.PoolError):
            if attempt < POOL_GET_RETRIES - 1:
                delay = POOL_GET_DELAY * (attempt + 1)
                if DEBUG:
                    logger.debug("db.pool_retry", delay_secs=round(delay, 1), attempt=attempt + 1, retries=POOL_GET_RETRIES)
                time.sleep(delay)
    logger.error("db.pool_exhausted", attempts=POOL_GET_RETRIES, pool_name='jobsPool')
    raise queue.Empty("All pool connections are in use")


def getConnection(e2eTests: bool = False) -> MySQLConnection:
    """Backward compatible wrapper for get_connection."""
    return get_connection(e2e_tests=e2eTests)
