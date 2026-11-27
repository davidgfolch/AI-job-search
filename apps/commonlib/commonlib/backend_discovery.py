"""Resolve the FastAPI backend URL with the shared LAN discovery stack.

Used by services that have to reach the backend without a bespoke URL setting:
an explicit ``BACKEND_URL`` pins the target, otherwise the usual Docker/host
candidates are probed via ``/health`` and, as a last resort, the LAN is scanned
with ``commonlib.network`` and cached by ``discovery_cache``.
"""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

from commonlib.direct_http import session as direct_session
from commonlib.environmentUtil import getEnv, getEnvBool
from commonlib.network.discovery import MAX_WORKERS, SCAN_TIMEOUT, get_local_ip, get_local_subnets, scan_port, subnet_hosts
from commonlib.network.discovery_cache import cached_discover
from commonlib.observability import get_logger
from commonlib.ollama_config import backend_candidate_urls

logger = get_logger("commonlib.backend_discovery")

BACKEND_URL_ENV = "BACKEND_URL"
BACKEND_PORT_ENV = "BACKEND_PORT"
BACKEND_DISCOVERY_ENV = "BACKEND_DISCOVERY"
PROBE_TIMEOUT_ENV = "BACKEND_PROBE_TIMEOUT"
DEFAULT_BACKEND_PORT = 8000
DEFAULT_PROBE_TIMEOUT = 10.0
HEALTH_PATH = "/health"
PROBE_TIMEOUT = float(os.getenv(PROBE_TIMEOUT_ENV, str(DEFAULT_PROBE_TIMEOUT)) or DEFAULT_PROBE_TIMEOUT)
_HTTP = direct_session()


def _port() -> int:
    try:
        return int(getEnv(BACKEND_PORT_ENV, str(DEFAULT_BACKEND_PORT)))
    except ValueError:
        return DEFAULT_BACKEND_PORT


def _with_port(url: str, port: int) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.hostname}:{port}"


def candidate_urls() -> tuple[str, ...]:
    """Configured URL only, or the shared candidates in topology order."""
    configured = (getEnv(BACKEND_URL_ENV) or "").strip()
    if configured:
        return (configured.rstrip("/"),)
    port = _port()
    urls = tuple(_with_port(url, port) for url in backend_candidate_urls())
    return urls if os.path.exists("/.dockerenv") else tuple(reversed(urls))


def verify_backend(url: str, timeout: float = PROBE_TIMEOUT) -> bool:
    """True when `url` answers the backend health endpoint (direct, no proxy)."""
    try:
        return _HTTP.get(f"{url.rstrip('/')}{HEALTH_PATH}", timeout=timeout).ok
    except Exception as ex:
        logger.warning("backend.probe_failed", url=url, error=str(ex))
        return False


def _scan_hosts(hosts: list[str], port: int) -> list[str]:
    found = []
    logger.info("backend.scan_started", hosts=len(hosts), port=port)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(scan_port, host, port, SCAN_TIMEOUT): host for host in hosts}
        for future in as_completed(futures):
            if future.result():
                found.append(futures[future])
    return found


def _discover_host(port: int, timeout: float, tried=()) -> str | None:
    def verify(host: str) -> bool:
        return verify_backend(f"http://{host}:{port}", timeout)

    def scan() -> list[str]:
        return _scan_hosts(subnet_hosts(get_local_subnets(), kind="backend"), port)

    return cached_discover("backend", verify, scan, tried=tried)


def get_backend_url(timeout: float = PROBE_TIMEOUT) -> str | None:
    """First reachable backend URL, or None when no candidate responds."""
    configured = (getEnv(BACKEND_URL_ENV) or "").strip()
    if configured:
        return configured.rstrip("/")
    for url in candidate_urls():
        if verify_backend(url, timeout):
            return url
    if not getEnvBool(BACKEND_DISCOVERY_ENV, False):
        return None
    port = _port()
    own_ip = get_local_ip()
    host = _discover_host(port, timeout, tried=(own_ip,) if own_ip else ())
    return f"http://{host}:{port}" if host else None
