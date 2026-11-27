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


WRITE_POOL_NAME = 'jobsPool'
READ_POOL_NAME = 'jobsReadPool'

_pool_initialized = False
_read_pool_initialized = False
_pool_lock = threading.Lock()
_read_pool_lock = threading.Lock()
_resolved_host: str | None = None


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


def _pool_size(env_key: str) -> int:
    """Pool size from `env_key`, defaulting to the write pool's configured size."""
    return int(os.getenv(env_key) or os.getenv('COMMONLIB_DB_POOL_SIZE', '5'))


def _create_pool(name: str, host: str, pool_size: int, e2e_tests: bool = False):
    conn = mysqlConnector.connect(
        host=host,
        user='root',
        password='rootPass',
        database=None if e2e_tests else get_db_name(),
        pool_name=name,
        pool_size=pool_size,
        pool_reset_session=True,
    )
    conn.close()


def _init_pool(e2e_tests: bool = False):
    """Initialize the write pool once (thread-safe) and remember the resolved host."""
    global _pool_initialized, _resolved_host
    if _pool_initialized:
        return
    with _pool_lock:
        if _pool_initialized:
            return
        _resolved_host = _resolve_db_host(e2e_tests)
        _create_pool(WRITE_POOL_NAME, _resolved_host, _pool_size('COMMONLIB_DB_POOL_SIZE'), e2e_tests)
        _pool_initialized = True


def _init_read_pool(e2e_tests: bool = False):
    """Initialize the read pool once (thread-safe).

    Reads default to the host the write pool resolved, so a burst of list queries
    cannot starve the writes of connections. Point `COMMONLIB_DB_READ_HOST` at a
    replica to move read load off the primary entirely.
    """
    global _read_pool_initialized
    if _read_pool_initialized:
        return
    with _read_pool_lock:
        if _read_pool_initialized:
            return
        _init_pool(e2e_tests)
        host = os.getenv('COMMONLIB_DB_READ_HOST', '').strip() or _resolved_host
        _create_pool(READ_POOL_NAME, host, _pool_size('COMMONLIB_DB_READ_POOL_SIZE'), e2e_tests)
        _read_pool_initialized = True
        logger.info("db.read_pool_ready", host=host, pool=READ_POOL_NAME)


def _get_from_pool(pool_name: str) -> MySQLConnection:
    """Take a connection from `pool_name`, retrying with backoff while it is exhausted."""
    for attempt in range(POOL_GET_RETRIES):
        try:
            conn = mysqlConnector.connect(pool_name=pool_name)
            if DEBUG:
                logger.debug("db.connection_opened", conn=repr(conn))
            return conn
        except (queue.Empty, mysqlConnector.errors.PoolError):
            if attempt < POOL_GET_RETRIES - 1:
                delay = POOL_GET_DELAY * (attempt + 1)
                if DEBUG:
                    logger.debug("db.pool_retry", delay_secs=round(delay, 1), attempt=attempt + 1, retries=POOL_GET_RETRIES)
                time.sleep(delay)
    logger.error("db.pool_exhausted", attempts=POOL_GET_RETRIES, pool_name=pool_name)
    raise queue.Empty("All pool connections are in use")


def get_connection(e2e_tests: bool = False) -> MySQLConnection:
    """
    Get a MySQL connection from the write pool.
    Caller MUST close the connection to return it to the pool.

    Retries with backoff when the pool is temporarily exhausted.

    Args:
        e2e_tests: If True, initializes pool without database (for E2E test setup)

    Returns:
        MySQL connection instance from pool
    """
    _init_pool(e2e_tests)
    return _get_from_pool(WRITE_POOL_NAME)


def get_read_connection(e2e_tests: bool = False) -> MySQLConnection:
    """Get a connection from the read-only pool.

    Meant for SELECT-only code paths; the write pool keeps its connections for
    inserts, updates and deletes. Caller MUST close the connection.
    """
    _init_read_pool(e2e_tests)
    return _get_from_pool(READ_POOL_NAME)


def getConnection(e2eTests: bool = False) -> MySQLConnection:
    """Backward compatible wrapper for get_connection."""
    return get_connection(e2e_tests=e2eTests)


def getReadConnection(e2eTests: bool = False) -> MySQLConnection:
    """Backward compatible wrapper for get_read_connection."""
    return get_read_connection(e2e_tests=e2eTests)
