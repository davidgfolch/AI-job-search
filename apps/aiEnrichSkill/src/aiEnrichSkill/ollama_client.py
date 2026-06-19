import os
import time
import requests

from commonlib.observability import get_logger

logger = get_logger("aiEnrichSkill.ollama_client")


def _get_num_predict() -> int:
    return int(os.getenv("AI_ENRICHSKILL_MAX_NEW_TOKENS", "2048"))


def ping_ollama(base_url: str = "http://localhost:11434", timeout: int = 5) -> bool:
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("ollama.ping_failed", error=str(e), base_url=base_url)
        return False


def _strip_provider_prefix(model: str) -> str:
    if "/" in model:
        return model.split("/", 1)[1]
    return model


def query_ollama(
    prompt: str,
    model: str = "ollama/qwen2.5:3b",
    base_url: str = "http://localhost:11434",
    timeout: int = 90,
    json_mode: bool = True,
) -> str | None:
    payload = {
        "model": _strip_provider_prefix(model),
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "num_predict": _get_num_predict()},
    }
    if json_mode:
        payload["format"] = "json"

    url = f"{base_url.rstrip('/')}/api/generate"

    for attempt, delay in enumerate([0, 1, 3]):
        if attempt > 0:
            logger.warning("ollama.retry", attempt=attempt, delay=delay)
            time.sleep(delay)
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            return resp.json().get("response", "")
        except Exception as e:
            logger.warning("ollama.error", attempt=attempt, error=str(e))

    logger.error("ollama.failed", model=model)
    return None
