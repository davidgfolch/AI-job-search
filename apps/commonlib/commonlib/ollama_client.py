"""Shared Ollama HTTP client used by the Ollama-backed AI enrichment modules.

Single implementation that both aiEnrich and aiEnrichSkill rely on. Each module
passes its configured primary URL (from `get_ollama_base_url()`); fallback
candidates are tried automatically when the primary server is unreachable, so a
down containerized Ollama transparently falls back to the host server.

Every candidate is pinged before the real job is sent: a liveness probe
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
from dataclasses import dataclass
from urllib.parse import urlsplit

import requests

from commonlib.observability import get_logger
from commonlib.ollama_config import (
    ollama_candidate_urls, get_num_predict, get_num_ctx, get_repeat_penalty, strip_provider_prefix,
)

logger = get_logger("commonlib.ollama_client")

OLLAMA_DISCOVERY_ENABLED = os.getenv("COMMONLIB_OLLAMA_DISCOVERY", "True").strip().lower() not in ("false", "0", "no")
OLLAMA_DISCOVERY_PORT = 11434
PROBE_TIMEOUT = 5
INFERENCE_PROBE_TIMEOUT = int(os.getenv("COMMONLIB_OLLAMA_PROBE_TIMEOUT", "30"))
PROBE_CACHE_SECONDS = int(os.getenv("COMMONLIB_OLLAMA_PROBE_CACHE_SECONDS", "300"))
AUTO_URL_SPECS = ("auto", "discover")
RETRY_DELAYS = (0, 1, 3)


@dataclass(frozen=True)
class OllamaResponse:
    text: str
    url: str
    model: str = ""
    done: bool = False
    done_reason: str | None = None
    total_duration: int | None = None
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_count: int | None = None
    eval_duration: int | None = None

    @property
    def truncated(self) -> bool:
        return self.done_reason == "length"


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


_logged_fallback_urls: set[str] = set()
_probed_servers: dict[str, float] = {}


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


def resolve_ollama_url(
    primary_url: str | None = None, timeout: int = PROBE_TIMEOUT, *, log=None
) -> str | None:
    """Return the URL of the first reachable Ollama server, or None if none respond."""
    log = log or logger
    if _is_auto_spec(primary_url):
        url = _discover_ollama_lan_url(log)
        if url is None:
            log.error("ollama.unreachable", candidates=(primary_url,))
        return url
    candidates = _candidate_urls(primary_url)
    tried = {_host_ip(url) for url in candidates}
    resolved = next((url for url in candidates if _ping_url(url, timeout, log)), None)
    if resolved is None:
        discovered = _discover_ollama_lan_url(log)
        resolved = discovered if discovered is not None and _host_ip(discovered) not in tried else None
    if resolved is None:
        log.error("ollama.unreachable", candidates=candidates)
        return None
    if resolved != candidates[0] and resolved not in _logged_fallback_urls:
        _logged_fallback_urls.add(resolved)
        log.info("ollama.fallback_active", base_url=resolved)
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


def _query_url(url: str, payload: dict, timeout: int, log) -> OllamaResponse | None:
    for attempt, delay in enumerate(RETRY_DELAYS):
        if attempt > 0:
            log.warning("ollama.retry", attempt=attempt, delay=delay, base_url=url)
            time.sleep(delay)
        try:
            log.info("ollama.dispatch", base_url=url, model=payload.get("model", ""))
            resp = requests.post(f"{url.rstrip('/')}/api/generate", json=payload, timeout=timeout)
            resp.raise_for_status()
            body = resp.json()
            if not isinstance(body, dict):
                raise ValueError("Ollama response is not a JSON object")
            return OllamaResponse(
                text=body.get("response") or "",
                url=url,
                model=body.get("model") or payload.get("model", ""),
                done=bool(body.get("done", False)),
                done_reason=body.get("done_reason"),
                total_duration=body.get("total_duration"),
                load_duration=body.get("load_duration"),
                prompt_eval_count=body.get("prompt_eval_count"),
                prompt_eval_duration=body.get("prompt_eval_duration"),
                eval_count=body.get("eval_count"),
                eval_duration=body.get("eval_duration"),
            )
        except requests.exceptions.ReadTimeout:
            log.warning("ollama.timeout", base_url=url, timeout=timeout)
            _probed_servers.pop(url, None)
            return None
        except Exception as e:
            log.warning("ollama.error", attempt=attempt, error=str(e), base_url=url)
    return None


def _generate_first_reachable(candidates, payload: dict, timeout: int, log) -> OllamaResponse | None:
    """Ping each candidate, then send the job to the first one that can run inference."""
    for url in candidates:
        if not _server_ready(url, payload, log):
            continue
        result = _query_url(url, payload, timeout, log)
        if result is not None:
            return result
    return None


def _log_response(result: OllamaResponse, log):
    log.info(
        "ollama.response",
        model=result.model,
        base_url=result.url,
        done=result.done,
        done_reason=result.done_reason,
        load_duration=result.load_duration,
        prompt_eval_count=result.prompt_eval_count,
        eval_count=result.eval_count,
        total_duration=result.total_duration,
    )


def query_ollama(
    prompt: str,
    model: str = "ollama/qwen2.5:3b",
    primary_url: str | None = None,
    timeout: int = 90,
    json_mode: bool = True,
    *,
    response_schema: dict | None = None,
    return_metadata: bool = False,
    log=None,
) -> str | OllamaResponse | None:
    log = log or logger
    num_predict = get_num_predict()
    num_ctx = get_num_ctx(prompt, num_predict)
    payload = {
        "model": strip_provider_prefix(model),
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": num_predict,
            "num_ctx": num_ctx,
            "repeat_penalty": get_repeat_penalty(),
        },
    }
    if json_mode:
        payload["format"] = response_schema or "json"
    log.info("ollama.request", model=model, prompt_length=len(prompt), num_predict=num_predict, num_ctx=num_ctx, schema=response_schema is not None)

    auto = _is_auto_spec(primary_url)
    if auto:
        discovered = _discover_ollama_lan_url(log)
        candidates = (discovered,) if discovered else ()
    else:
        candidates = _candidate_urls(primary_url)
    tried = {_host_ip(url) for url in candidates}
    result = _generate_first_reachable(candidates, payload, timeout, log)
    if result is None and not auto:
        # Last resort: LAN discovery, unless it only leads back to an already-tried host
        # (host.docker.internal and its gateway IP are the same server under two names).
        discovered = _discover_ollama_lan_url(log)
        if discovered is not None and _host_ip(discovered) not in tried:
            result = _generate_first_reachable((discovered,), payload, timeout, log)
    if result is None:
        log.error("ollama.failed", model=model)
        return None
    _log_response(result, log)
    return result if return_metadata else result.text
