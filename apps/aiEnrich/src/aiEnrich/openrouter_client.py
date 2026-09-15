import json
import os
import re
import time

from openai import OpenAI
from commonlib.observability import get_logger

logger = get_logger("aiEnrich.openrouter_client")

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openrouter/free"
DEFAULT_FALLBACK_MODEL = "nex-agi/nex-n2.5-pro:free"
RETRIES_PER_MODEL = 3

SYSTEM_PROMPT = "You are a technical job data extractor. Given a job posting, extract structured data as valid JSON."


def _get_max_tokens() -> int:
    return int(os.getenv("AI_ENRICH_MAX_NEW_TOKENS", "2048"))


def _get_api_key() -> str:
    key = os.getenv("AI_ENRICH_OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        raise ValueError("AI_ENRICH_OPENROUTER_API_KEY (or OPENROUTER_API_KEY) is not set")
    return key


def _strip_fences(raw: str) -> str:
    return re.sub(r'```(json)?\n?', '', raw).strip()


def _is_valid_json(raw: str) -> bool:
    try:
        json.loads(_strip_fences(raw))
        return True
    except Exception:
        return False


def ping_openrouter(base_url: str = DEFAULT_BASE_URL, timeout: int = 5) -> bool:
    try:
        client = OpenAI(base_url=base_url, api_key=_get_api_key(), timeout=timeout)
        client.models.list()
        return True
    except Exception as e:
        logger.error("openrouter.ping_failed", error=str(e), base_url=base_url)
        return False


def query_openrouter(
    prompt: str,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 90,
    json_mode: bool = False,
    fallback_model: str | None = None,
) -> str | None:
    api_key = _get_api_key()
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)
    last_raw = None

    models = [(model, json_mode)]
    if fallback_model and fallback_model != model:
        models.append((fallback_model, True))

    for target, use_json in models:
        if last_raw:
            logger.warning("openrouter.fallback_used", primary=model, fallback=target)
            last_raw = None
        delays = [0, 1, 3]
        for attempt, delay in enumerate(delays[:RETRIES_PER_MODEL]):
            if attempt > 0:
                logger.warning("openrouter.retry", attempt=attempt, delay=delay, model=target)
                time.sleep(delay)
            kwargs: dict = {}
            if use_json:
                kwargs["response_format"] = {"type": "json_object"}
            try:
                response = client.chat.completions.create(
                    model=target,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=_get_max_tokens(),
                    temperature=0,
                    **kwargs,
                )
                if not response.choices:
                    logger.warning("openrouter.empty_response", attempt=attempt, model=target)
                    continue
                content = response.choices[0].message.content
                if content is None:
                    logger.warning("openrouter.null_content", attempt=attempt, model=target)
                    continue
                result = content.strip()
                if not result:
                    logger.warning("openrouter.empty_content", attempt=attempt, model=target)
                    continue
                last_raw = result
                if _is_valid_json(result):
                    return result
                logger.warning("openrouter.invalid_json", attempt=attempt, model=target, raw=result[:200])
            except Exception as e:
                logger.warning("openrouter.error", attempt=attempt, error=str(e), model=target)

    logger.error("openrouter.failed", model=model, fallback=fallback_model)
    return last_raw if last_raw else None
