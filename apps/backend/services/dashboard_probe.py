import socket
import urllib.request
from urllib.parse import urlsplit

from commonlib.observability import get_logger
from commonlib.ollama_probe import get_last_ollama_server, resolve_ollama_url

logger = get_logger("backend.services.dashboard_probe")

OLLAMA_PROBE_TIMEOUT_SECONDS = 3
LOCAL_HOSTS = {"localhost", "127.0.0.1", "host.docker.internal", "ollama"}


def _host_ip(url: str) -> str | None:
    host = urlsplit(url).hostname or ""
    try:
        return socket.gethostbyname(host)
    except Exception:
        return None


def _is_lan_url(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    if host in LOCAL_HOSTS:
        return False
    ip = _host_ip(url)
    return bool(ip) and not ip.startswith("127.")


def _ollama_info(url: str | None) -> dict:
    """Build the ollama info dict for a given URL (None => unreachable)."""
    if url is None:
        last = get_last_ollama_server()
        return {
            "reachable": False,
            "serverUrl": last.get("url"),
            "serverIp": last.get("ip"),
            "isLan": bool(last.get("is_lan")),
        }
    return {
        "reachable": True,
        "serverUrl": url,
        "serverIp": _host_ip(url),
        "isLan": _is_lan_url(url),
    }


def _probe_ollama() -> dict:
    """Return Ollama server info, probing the last-known server first (no cache).

    The last-known server IP:port is probed with a fresh request every time, so
    a server that came back up is detected immediately instead of waiting out a
    TTL. If it no longer answers, the configured candidates and LAN scan are
    tried as fallbacks, and any newly found server becomes the new last-known.
    The last-known server address is always reported (even when unreachable) so
    the dashboard keeps showing the previously detected server instead of going
    blank."""
    last = get_last_ollama_server()
    last_url = last.get("url")

    # 1. Probe the last-known server directly, fresh, no cache.
    if last_url:
        try:
            with urllib.request.urlopen(f"{last_url.rstrip('/')}/api/version", timeout=OLLAMA_PROBE_TIMEOUT_SECONDS) as resp:
                if resp.status == 200:
                    return _ollama_info(last_url)
        except Exception as e:
            logger.debug("ollama.last_known_probe_failed", error=str(e), url=last_url)

    # 2. Last-known is down: try configured candidates + LAN scan.
    resolved = resolve_ollama_url(timeout=OLLAMA_PROBE_TIMEOUT_SECONDS, log=logger)
    if resolved is not None:
        return _ollama_info(resolved)

    # 3. Nothing reachable: report the last-known address as unreachable.
    return _ollama_info(None)
