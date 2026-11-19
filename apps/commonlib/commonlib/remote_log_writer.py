"""Ship scrapper records to a backend on another machine.

When the scrapper runs on a different LAN box, its local JSONL never reaches the
backend that serves ``/api/statistics/keywords``. This module buffers the records
structlog already writes and POSTs them in batches to the backend, which appends them
to the same JSONL file the statistics endpoint reads.

The backend is resolved by ``commonlib.backend_discovery`` using the shared
``BACKEND_URL`` / ``BACKEND_PORT`` / ``BACKEND_DISCOVERY`` settings. Shipping is
skipped for a loopback target: a local backend already shares the log directory
through Compose, so shipping would duplicate every record.

| Variable | Default | Meaning |
|---|---|---|
| `SCRAPPER_LOG_BATCH_SIZE` | `200` | Records per POST |
| `SCRAPPER_LOG_FLUSH_SECONDS` | `5` | Background flush interval |
"""
import atexit
import json
import threading
import time
from urllib.parse import urlparse

from commonlib.direct_http import session as direct_session
from commonlib.environmentUtil import getEnv
from commonlib.log_writer import public_record

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
_HTTP = direct_session()


def is_remote_url(url: str | None) -> bool:
    """True for an explicit URL with a non-loopback host."""
    host = (urlparse(url or "").hostname or "").lower()
    local = host in LOOPBACK_HOSTS or host.startswith("127.") or host.endswith(".localhost")
    return bool(host) and not local


def _log(event: str, level: str, **fields) -> None:
    from commonlib.observability import get_logger  # local: observability imports this module
    _local.shipping = True
    try:
        getattr(get_logger("commonlib.remote_log_writer"), level)(event, **fields)
    finally:
        _local.shipping = False


def _warning(event: str, **fields) -> None:
    _log(event, "warning", **fields)


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
        response = _HTTP.post(
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


def _discovered_backend_url() -> str | None:
    from commonlib.backend_discovery import get_backend_url  # local: discovery imports observability
    return get_backend_url()


def configure_remote_logging(base_url: str = None, app_name: str = "scrapper", timeout: float = DEFAULT_TIMEOUT, start_thread: bool = True) -> bool:
    """Enable shipping to `base_url` (or the discovered backend) and return whether it is active."""
    global _config
    url = base_url if base_url is not None else _discovered_backend_url()
    with _lock:
        _buffer.clear()
    if not is_remote_url(url):
        _config = None
        _log("remote_logs.disabled", "info", reason="local_or_unreachable_backend", url=url)
        return False
    _config = {
        "base_url": url.rstrip("/"),
        "app_name": app_name,
        "batch_size": max(1, int(getEnv(BATCH_SIZE_ENV, DEFAULT_BATCH_SIZE))),
        "timeout": float(timeout),
    }
    _log("remote_logs.enabled", "info", base_url=_config["base_url"], app_name=app_name)
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
