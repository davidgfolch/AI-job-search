"""Server selection for the Ollama-backed AI enrichment modules.

Split out of `ollama_client` (which builds and dispatches the actual job): this
module answers *where* a job should run — the configured fallback candidates,
the LAN discovery scan, the `/api/tags` liveness ping and the one-token
inference probe.

Every candidate is probed before the real job is sent: a liveness probe
(`GET /api/tags`) picks the reachable server, then a one-token generation
(`POST /api/generate`) confirms it can actually run inference, so a server that
answers the API but has a wedged runner is skipped instead of blocking the whole
generation timeout. When no configured candidate answers, the LAN is scanned for
an Ollama server on port 11434 unless `COMMONLIB_OLLAMA_DISCOVERY` is disabled;
passing `auto` (or `discover`) as the primary URL goes straight to it.
"""
import os
import socket
import time
from collections.abc import Iterator
from urllib.parse import urlsplit

import requests

from commonlib.observability import get_logger
from commonlib.ollama_config import ollama_candidate_urls

logger = get_logger("commonlib.ollama_probe")

OLLAMA_DISCOVERY_ENABLED = os.getenv("COMMONLIB_OLLAMA_DISCOVERY", "True").strip().lower() not in ("false", "0", "no")
OLLAMA_DISCOVERY_PORT = 11434
PROBE_TIMEOUT = 5
INFERENCE_PROBE_TIMEOUT = int(os.getenv("COMMONLIB_OLLAMA_PROBE_TIMEOUT", "30"))
PROBE_CACHE_SECONDS = int(os.getenv("COMMONLIB_OLLAMA_PROBE_CACHE_SECONDS", "300"))
AUTO_URL_SPECS = ("auto", "discover")

_logged_fallback_urls: set[str] = set()
_probed_servers: dict[str, float] = {}
_LAST_OLLAMA_SERVER: dict = {"url": None, "ip": None, "is_lan": False}
_OLLAMA_LOCAL_HOSTS = {"localhost", "127.0.0.1", "host.docker.internal", "ollama"}


def get_last_ollama_server() -> dict:
    """Last-known reachable Ollama server, shared by all modules in this process.

    Modules that need to reach Ollama (backend dashboard, aiEnrich, aiEnrichSkill,
    …) read this instead of rediscovering from scratch, so they all agree on the
    same server until it stops answering."""
    return dict(_LAST_OLLAMA_SERVER)


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


def _candidate_urls(primary_url: str | None) -> tuple[str, ...]:
    return ollama_candidate_urls(primary_url)


def _is_auto_spec(primary_url: str | None) -> bool:
    """True when the configured primary URL asks for LAN discovery instead of a host."""
    return isinstance(primary_url, str) and primary_url.strip().lower() in AUTO_URL_SPECS


def _host_ip(url: str) -> str:
    """Identity of a server for deduplication: its IP, so one host reached under two names counts once."""
    host = urlsplit(url).hostname or url
    try:
        return socket.gethostbyname(host)
    except Exception:
        return host


def _discover_ollama_lan_url(log=None) -> str | None:
    """Scan the LAN for an Ollama server, or None when disabled / nothing is found."""
    if not OLLAMA_DISCOVERY_ENABLED:
        return None
    log = log or logger
    try:
        from commonlib.network.ollama_discovery import auto_discover_host
        host = auto_discover_host()
    except Exception as e:
        log.warning("ollama.discovery_failed", error=str(e))
        return None
    if not host:
        return None
    url = f"http://{host}:{OLLAMA_DISCOVERY_PORT}"
    log.info("ollama.lan_discovered", base_url=url)
    return url


def _ping_url(url: str, timeout: int, log) -> bool:
    try:
        resp = requests.get(f"{url.rstrip('/')}/api/tags", timeout=timeout)
        resp.raise_for_status()
        return True
    except Exception as e:
        log.debug("ollama.probe_failed", error=str(e), base_url=url)
        return False


def resolve_ollama_url(primary_url: str | None = None, timeout: int = PROBE_TIMEOUT, *, log=None) -> str | None:
    """Return the URL of the first reachable Ollama server, or None if none respond.

    The last-known server (from a previous successful discovery) is probed first
    with a fresh request — no cache — so a server that came back up is detected
    immediately instead of waiting out a TTL. If it no longer answers, the
    configured candidates and the LAN scan are tried as fallbacks."""
    log = log or logger
    # 1. Last-known server first: fresh probe, no cache.
    last = get_last_ollama_server()
    last_url = last.get("url") if last else None
    if last_url and _ping_url(last_url, timeout, log):
        return last_url
    # 2. auto spec -> straight to LAN discovery.
    if _is_auto_spec(primary_url):
        url = _discover_ollama_lan_url(log)
        if url is None:
            log.error("ollama.unreachable", candidates=(primary_url,))
        else:
            _record_ollama_server(url, log)
        return url
    # 3. Configured candidates, then LAN scan as a last resort.
    candidates = _candidate_urls(primary_url)
    tried = {_host_ip(url) for url in candidates}
    resolved = next((url for url in candidates if _ping_url(url, timeout, log)), None)
    if resolved is None:
        discovered = _discover_ollama_lan_url(log)
        resolved = discovered if discovered is not None and _host_ip(discovered) not in tried else None
    if resolved is not None:
        _record_ollama_server(resolved, log)
        if resolved != candidates[0] and resolved not in _logged_fallback_urls:
            _logged_fallback_urls.add(resolved)
            log.info("ollama.fallback_active", base_url=resolved)
    else:
        log.error("ollama.unreachable", candidates=candidates)
    return resolved


def ping_ollama(primary_url: str | None = None, timeout: int = PROBE_TIMEOUT, *, log=None) -> bool:
    return resolve_ollama_url(primary_url=primary_url, timeout=timeout, log=log) is not None


def _probe_inference(url: str, model: str, options: dict | None, log) -> bool:
    """Ask for a single token before the real job: a server whose runner is stuck
    answers `/api/tags` but never returns from `/api/generate`, so only this probe
    can rule it out without paying the whole generation timeout.

    The job's own options are reused and only `num_predict` shrinks: a different
    `num_ctx` makes Ollama reload the model, once for the probe and again for the job."""
    payload = {"model": model, "prompt": "ping", "stream": False, "options": {**(options or {}), "num_predict": 1}}
    try:
        resp = requests.post(f"{url.rstrip('/')}/api/generate", json=payload, timeout=INFERENCE_PROBE_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        log.warning("ollama.inference_probe_failed", error=str(e), base_url=url, timeout=INFERENCE_PROBE_TIMEOUT)
        return False
    log.info("ollama.inference_probe_ok", base_url=url, model=model)
    return True


def _server_ready(url: str, payload: dict, log) -> bool:
    """Probe a server at most once per `PROBE_CACHE_SECONDS`: the first success is
    remembered and every following job goes straight to inference instead of
    re-connecting. A timeout or a failed probe drops it, so a wedged runner is
    detected again by the next job rather than trusted forever."""
    now = time.monotonic()
    last_ok = _probed_servers.get(url)
    if last_ok is not None and now - last_ok < PROBE_CACHE_SECONDS:
        return True
    if not _probe_inference(url, payload.get("model", ""), payload.get("options"), log):
        _probed_servers.pop(url, None)
        return False
    _probed_servers[url] = now
    return True


def forget_server(url: str) -> None:
    """Drop the probe cache entry of `url`: a job that timed out means the server
    went away mid-flight, so the next job must probe it again instead of trusting it."""
    _probed_servers.pop(url, None)


def healthy_urls(primary_url: str | None, payload: dict, log) -> Iterator[str]:
    """Yield, in try order, the servers that should receive `payload`.

    Candidates are probed lazily: the caller only asks for the next URL after its
    query to the previous one got nothing, so the servers down the list are not
    even probed while the current one still answers. When every configured
    candidate is exhausted, the LAN discovery result is offered as a last resort,
    unless it only leads back to an already-tried host (`host.docker.internal`
    and its gateway IP are the same server under two names)."""
    if _is_auto_spec(primary_url):
        discovered = _discover_ollama_lan_url(log)
        if discovered is not None and _server_ready(discovered, payload, log):
            yield discovered
        return
    candidates = _candidate_urls(primary_url)
    tried = {_host_ip(url) for url in candidates}
    for url in candidates:
        if _server_ready(url, payload, log):
            yield url
    discovered = _discover_ollama_lan_url(log)
    if discovered is not None and _host_ip(discovered) not in tried and _server_ready(discovered, payload, log):
        yield discovered
