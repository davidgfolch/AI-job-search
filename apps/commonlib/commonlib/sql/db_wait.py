"""Block until MySQL answers, instead of exiting into a restart storm.

Compose applies `depends_on: service_healthy` only to the start it orchestrates.
A resumed stack restarts `unless-stopped` containers without that gate, so a
worker that exits on a missing database turns into a restart storm that starves
the very database it is waiting for. Waiting here keeps the container alive and
idle until MySQL is up.
"""
import os
import time

from commonlib.observability import get_logger

logger = get_logger("commonlib.sql.db_wait")

DB_WAIT_INTERVAL = float(os.getenv('COMMONLIB_DB_WAIT_INTERVAL', '2'))
DB_WAIT_LOG_SECONDS = float(os.getenv('COMMONLIB_DB_WAIT_LOG_SECONDS', '30'))


def wait_timeout() -> float:
    """`COMMONLIB_DB_WAIT_TIMEOUT` in seconds (0 = wait forever)."""
    try:
        return float(os.getenv('COMMONLIB_DB_WAIT_TIMEOUT', '0') or 0)
    except ValueError:
        return 0.0


def wait_for_db(timeout: float | None = None, interval: float | None = None, log=None, resolve=None) -> bool:
    """Block until MySQL resolves, logging periodically.

    `timeout` defaults to `COMMONLIB_DB_WAIT_TIMEOUT` (0 = forever); a positive
    value returns False when it expires. `resolve` is injectable for tests and
    defaults to `connection_manager._resolve_db_host`.
    """
    from commonlib.sql.connection_manager import _resolve_db_host

    log = log or logger
    resolve = resolve or _resolve_db_host
    interval = DB_WAIT_INTERVAL if interval is None else interval
    timeout = wait_timeout() if timeout is None else timeout
    deadline = time.monotonic() + timeout if timeout > 0 else None
    started = time.monotonic()
    last_log = 0.0
    while True:
        try:
            host = resolve()
            log.info("db.ready", host=host, waited_secs=round(time.monotonic() - started, 1))
            return True
        except ConnectionError as e:
            waited = time.monotonic() - started
            if deadline is not None and time.monotonic() >= deadline:
                log.error("db.wait_timeout", waited_secs=round(waited, 1), error=str(e))
                return False
            if waited - last_log >= DB_WAIT_LOG_SECONDS:
                last_log = waited
                log.warning("db.waiting", waited_secs=round(waited, 1))
            time.sleep(interval)
