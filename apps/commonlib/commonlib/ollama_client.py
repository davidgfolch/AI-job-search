"""Shared Ollama HTTP client used by the Ollama-backed AI enrichment modules.

Single implementation that both aiEnrich and aiEnrichSkill rely on. Each module
passes its configured primary URL (from `get_ollama_base_url()`); fallback
candidates are tried automatically when the primary server is unreachable, so a
down containerized Ollama transparently falls back to the host server.
"""
import time
import requests

from commonlib.environmentUtil import getEnv
from commonlib.observability import get_logger
from commonlib.ollama_config import ollama_candidate_urls

logger = get_logger("commonlib.ollama_client")

MAX_NEW_TOKENS_ENVS = ("AI_ENRICH_MAX_NEW_TOKENS", "AI_ENRICHSKILL_MAX_NEW_TOKENS")


def _get_num_predict() -> int:
    for env in MAX_NEW_TOKENS_ENVS:
        value = getEnv(env)
        if value:
            return int(value)
    return 2048


def _candidate_urls(primary_url: str | None) -> tuple[str, ...]:
    return ollama_candidate_urls(primary_url)


def _strip_provider_prefix(model: str) -> str:
    if "/" in model:
        return model.split("/", 1)[1]
    return model


def resolve_ollama_url(
    primary_url: str | None = None, timeout: int = 5, *, log=None
) -> str | None:
    """Return the URL of the first reachable Ollama server, or None if none respond."""
    log = log or logger
    candidates = _candidate_urls(primary_url)
    for url in candidates:
        try:
            resp = requests.get(f"{url.rstrip('/')}/api/tags", timeout=timeout)
            resp.raise_for_status()
            if url != candidates[0]:
                log.info("ollama.fallback_active", base_url=url)
            return url
        except Exception as e:
            log.debug("ollama.probe_failed", error=str(e), base_url=url)
    log.error("ollama.unreachable", candidates=candidates)
    return None


def ping_ollama(primary_url: str | None = None, timeout: int = 5, *, log=None) -> bool:
    return resolve_ollama_url(primary_url=primary_url, timeout=timeout, log=log) is not None


def _query_url(url: str, payload: dict, timeout: int, log) -> str | None:
    for attempt, delay in enumerate([0, 1, 3]):
        if attempt > 0:
            log.warning("ollama.retry", attempt=attempt, delay=delay, base_url=url)
            time.sleep(delay)
        try:
            resp = requests.post(f"{url.rstrip('/')}/api/generate", json=payload, timeout=timeout)
            resp.raise_for_status()
            return resp.json().get("response", "")
        except Exception as e:
            log.warning("ollama.error", attempt=attempt, error=str(e), base_url=url)
    return None


def query_ollama(
    prompt: str,
    model: str = "ollama/qwen2.5:3b",
    primary_url: str | None = None,
    timeout: int = 90,
    json_mode: bool = True,
    *,
    log=None,
) -> str | None:
    log = log or logger
    payload = {
        "model": _strip_provider_prefix(model),
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "num_predict": _get_num_predict()},
    }
    if json_mode:
        payload["format"] = "json"

    for url in _candidate_urls(primary_url):
        result = _query_url(url, payload, timeout, log)
        if result is not None:
            return result

    log.error("ollama.failed", model=model)
    return None