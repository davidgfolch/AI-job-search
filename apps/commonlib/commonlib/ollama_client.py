"""Shared Ollama HTTP client used by the Ollama-backed AI enrichment modules.

Single implementation that both aiEnrich and aiEnrichSkill rely on. Each module
passes its configured primary URL (from `get_ollama_base_url()`); fallback
candidates are tried automatically when the primary server is unreachable, so a
down containerized Ollama transparently falls back to the host server.

Server selection lives in `commonlib.ollama_probe`: `healthy_urls()` yields the
configured candidates (or the LAN discovery result), each one gated by the
liveness and one-token inference probes. This module owns the rest of the job:
building the payload, dispatching it with retries to the first server that can
run inference, and normalizing the reply into `OllamaResponse`.
"""
import time
from dataclasses import dataclass

import requests

from commonlib.observability import get_logger
from commonlib.ollama_config import get_num_predict, get_num_ctx, get_repeat_penalty, strip_provider_prefix
from commonlib.ollama_probe import (  # re-exports: existing importers treat this module as the entry point
    INFERENCE_PROBE_TIMEOUT, PROBE_TIMEOUT, _ping_url, forget_server, healthy_urls, ping_ollama, resolve_ollama_url,
)

logger = get_logger("commonlib.ollama_client")
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
            forget_server(url)
            return None
        except Exception as e:
            log.warning("ollama.error", attempt=attempt, error=str(e), base_url=url)
    return None


def _generate_first_reachable(primary_url: str | None, payload: dict, timeout: int, log) -> OllamaResponse | None:
    """Send the job to each server `healthy_urls` considers capable of running it;
    the generator probes lazily, so a candidate is only considered after the
    previous one returned nothing."""
    for url in healthy_urls(primary_url, payload, log):
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

    result = _generate_first_reachable(primary_url, payload, timeout, log)
    if result is None:
        log.error("ollama.failed", model=model)
        return None
    _log_response(result, log)
    return result if return_metadata else result.text
