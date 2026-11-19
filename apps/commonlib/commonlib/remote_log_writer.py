"""Ship scrapper records to a backend on another machine.

When the scrapper runs on a different LAN box, its local JSONL never reaches the
backend that serves ``/api/statistics/keywords``. This module buffers the records
structlog already writes and POSTs them in batches to the backend, which appends them
to the same JSONL file the statistics endpoint reads.

Shipping is opt-in through ``SCRAPPER_LOG_BACKEND_URL`` and is ignored for loopback
URLs: a local backend already shares the log directory through Compose, so shipping
would duplicate every record.

| Variable | Default | Meaning |
|---|---|---|
| `SCRAPPER_LOG_BACKEND_URL` | unset | Base URL of the backend receiving scrapper logs |
| `SCRAPPER_LOG_BATCH_SIZE` | `200` | Records per POST |
| `SCRAPPER_LOG_FLUSH_SECONDS` | `5` | Background flush interval |
"""
import atexit
import json
import threading
import time
from urllib.parse import urlparse

import requests

from commonlib.environmentUtil import getEnv
from commonlib.log_writer import public_record

LOG_BACKEND_ENV = "SCRAPPER_LOG_BACKEND_URL"
BATCH_SIZE_ENV = "SCRAPPER_LOG_BATCH_SIZE"
FLUSH_SECONDS_ENV = "SCRAPPER_LOG_FLUSH_SECONDS"
INGEST_PATH = "/api/scrapper/logs"
LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
OWN_EVENT_PREFIX = "remote_logs."
DEFAULT_BATCH_SIZE = 200
DEFAULT_FLUSH_SECONDS = 5.0
DEFAULT_TIMEOUT = 5.0

_lock = threading.Lock()
_buffer: list = []
_config: dict | None = None
_local = threading.local()


def is_remote_url(url: str | None) -> bool:
    """True for an explicit URL with a non-loopback host."""
    host = (urlparse(url or "").hostname or "").lower()
    local = host in LOOPBACK_HOSTS or host.startswith("127.") or host.endswith(".localhost")
    return bool(host) and not local


def _warning(event: str, **fields) -> None:
    from commonlib.observability import get_logger  # local: observability imports this module
    _local.shipping = True
    try:
        get_logger("commonlib.remote_log_writer").warning(event, **fields)
    finally:
        _local.shipping = False


def flush_remote_logs() -> None:
    """POST the buffered records once; keep them for a later retry if rejected."""
    config = _config
    if not config:
        return
    with _lock:
        if not _buffer:
            return
        batch = list(_buffer)
    payload = json.dumps({"app": config["app_name"], "records": batch}, default=str)
    _local.shipping = True
    try:
        response = requests.post(
            f"{config['base_url']}{INGEST_PATH}", data=payload,
            headers={"Content-Type": "application/json"}, timeout=config["timeout"])
    except Exception as ex:
        _warning("remote_logs.failed", error=str(ex), count=len(batch))
        return
    finally:
        _local.shipping = False
    if not response.ok:
        _warning("remote_logs.rejected", status_code=response.status_code, count=len(batch))
        return
    with _lock:
        del _buffer[:len(batch)]


def _flush_loop(interval: float) -> None:
    while True:
        time.sleep(interval)
        flush_remote_logs()


def configure_remote_logging(base_url: str = None, app_name: str = "scrapper", timeout: float = DEFAULT_TIMEOUT, start_thread: bool = True) -> bool:
    """Enable shipping to `base_url` (or the configured env var) and return whether it is active."""
    global _config
    url = base_url if base_url is not None else getEnv(LOG_BACKEND_ENV)
    with _lock:
        _buffer.clear()
    if not is_remote_url(url):
        _config = None
        return False
    _config = {
        "base_url": url.rstrip("/"),
        "app_name": app_name,
        "batch_size": max(1, int(getEnv(BATCH_SIZE_ENV, DEFAULT_BATCH_SIZE))),
        "timeout": float(timeout),
    }
    if start_thread:
        interval = float(getEnv(FLUSH_SECONDS_ENV, DEFAULT_FLUSH_SECONDS))
        threading.Thread(target=_flush_loop, args=(interval,), daemon=True, name="remote-log-shipper").start()
    atexit.register(flush_remote_logs)
    return True


def remote_log_processor(logger, method_name, event_dict: dict) -> dict:  # noqa: ARG001 - structlog processor signature
    """Buffer an app record for shipping; never ship diagnostics or other apps' records."""
    config = _config
    if not config or getattr(_local, "shipping", False):
        return event_dict
    if str(event_dict.get("event", "")).startswith(OWN_EVENT_PREFIX):
        return event_dict
    if event_dict.get("logger") and event_dict["logger"] != config["app_name"]:
        return event_dict
    with _lock:
        _buffer.append(public_record(dict(event_dict)))
        limit = config["batch_size"] * 5
        if len(_buffer) > limit:
            del _buffer[:len(_buffer) - limit]
        full = len(_buffer) >= config["batch_size"]
    if full:
        flush_remote_logs()
    return event_dict
