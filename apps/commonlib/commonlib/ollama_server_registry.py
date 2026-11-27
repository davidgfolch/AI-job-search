"""Where the Ollama-backed modules find their server.

Split out of `ollama_probe` (which re-exports the entry points): this module owns the
process-wide *learned* server and the LAN discovery scan, while `ollama_probe` owns the
liveness/inference probes and the try order over the configured candidates.
"""
import os
import socket
from urllib.parse import urlsplit

from commonlib.observability import get_logger

logger = get_logger("commonlib.ollama_server_registry")

OLLAMA_DISCOVERY_ENABLED = os.getenv("COMMONLIB_OLLAMA_DISCOVERY", "True").strip().lower() not in ("false", "0", "no")
OLLAMA_DISCOVERY_PORT = 11434
AUTO_URL_SPECS = ("auto", "discover")

_LAST_OLLAMA_SERVER: dict = {"url": None, "ip": None, "is_lan": False}
_OLLAMA_LOCAL_HOSTS = {"localhost", "127.0.0.1", "host.docker.internal", "ollama"}


def get_last_ollama_server() -> dict:
    """Last-known reachable Ollama server, shared by all modules in this process.

    Modules that need to reach Ollama (backend dashboard, aiEnrich, aiEnrichSkill,
    …) read this instead of rediscovering from scratch, so they all agree on the
    same server until it stops answering."""
    return dict(_LAST_OLLAMA_SERVER)


def _host_ip(url: str) -> str:
    """Identity of a server for deduplication: its IP, so one host reached under two names counts once."""
    host = urlsplit(url).hostname or url
    try:
        return socket.gethostbyname(host)
    except Exception:
        return host


def _is_lan_url(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    if host in _OLLAMA_LOCAL_HOSTS:
        return False
    ip = _host_ip(url)
    return bool(ip) and not ip.startswith("127.")


def _record_ollama_server(url: str, log) -> None:
    """Remember `url` as the last-known Ollama server (IP + LAN scope)."""
    ip = _host_ip(url)
    is_lan = _is_lan_url(url)
    _LAST_OLLAMA_SERVER.update({"url": url, "ip": ip, "is_lan": is_lan})
    log.info("ollama.server_learned", base_url=url, ip=ip, lan=is_lan)


def _discover_ollama_lan_url(log=None) -> str | None:
    """Scan the LAN for an Ollama server, or None when disabled / nothing is found."""
    if not OLLAMA_DISCOVERY_ENABLED:
        return None
    log = log or logger
    try:
        from commonlib.network.ollama_resolve import auto_discover_host
        host = auto_discover_host()
    except Exception as e:
        log.warning("ollama.discovery_failed", error=str(e))
        return None
    if not host:
        return None
    url = f"http://{host}:{OLLAMA_DISCOVERY_PORT}"
    log.info("ollama.lan_discovered", base_url=url)
    return url
