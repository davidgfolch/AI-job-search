"""Shared Ollama HTTP client used by the Ollama-backed AI enrichment modules.

Single implementation that both aiEnrich and aiEnrichSkill rely on. Each module
passes its configured primary URL (from `get_ollama_base_url()`); fallback
candidates are tried automatically when the primary server is unreachable, so a
down containerized Ollama transparently falls back to the host server.
"""
import time
from dataclasses import dataclass

import requests

from commonlib.observability import get_logger
from commonlib.ollama_config import (
    ollama_candidate_urls, get_num_predict, get_num_ctx, get_repeat_penalty, strip_provider_prefix,
)

logger = get_logger("commonlib.ollama_client")


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


_logged_fallback_urls: set[str] = set()


def resolve_ollama_url(
    primary_url: str | None = None, timeout: int = 5, *, log=None
) -> str | None:
    """Return the URL of the first reachable Ollama server, or None if none respond."""
    global _logged_fallback_urls
    log = log or logger
    candidates = _candidate_urls(primary_url)
    for url in candidates:
        try:
            resp = requests.get(f"{url.rstrip('/')}/api/tags", timeout=timeout)
            resp.raise_for_status()
            if url != candidates[0] and url not in _logged_fallback_urls:
                _logged_fallback_urls.add(url)
                log.info("ollama.fallback_active", base_url=url)
            return url
        except Exception as e:
            log.debug("ollama.probe_failed", error=str(e), base_url=url)
    log.error("ollama.unreachable", candidates=candidates)
    return None


def ping_ollama(primary_url: str | None = None, timeout: int = 5, *, log=None) -> bool:
    return resolve_ollama_url(primary_url=primary_url, timeout=timeout, log=log) is not None


def _query_url(url: str, payload: dict, timeout: int, log) -> OllamaResponse | None:
    for attempt, delay in enumerate([0, 1, 3]):
        if attempt > 0:
            log.warning("ollama.retry", attempt=attempt, delay=delay, base_url=url)
            time.sleep(delay)
        try:
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
            return None
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

    for url in _candidate_urls(primary_url):
        result = _query_url(url, payload, timeout, log)
        if result is not None:
            log.info(
                "ollama.response",
                model=result.model,
                base_url=result.url,
                done=result.done,
                done_reason=result.done_reason,
                prompt_eval_count=result.prompt_eval_count,
                eval_count=result.eval_count,
                total_duration=result.total_duration,
            )
            return result if return_metadata else result.text

    log.error("ollama.failed", model=model)
    return None
