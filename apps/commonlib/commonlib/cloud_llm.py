"""Shared OpenAI-compatible client for the free-tier cloud LLM providers.

Every worker uses the same registry, key lookup and chat-completion request so a
provider added to Settings works everywhere without a vendor SDK in each module.
"""
import time
from dataclasses import dataclass

import requests

from commonlib.envFileUtil import getEnvFile
from commonlib.observability import get_logger
from commonlib.ollama_config import get_configured_ollama_url, ollama_probe_urls

logger = get_logger("commonlib.cloud_llm")

MAX_MODELS = 500

OPENROUTER = "openrouter"
GEMINI = "gemini"
GROQ = "groq"
CEREBRAS = "cerebras"
HF_INFERENCE = "hf-inference"


@dataclass(frozen=True)
class ProviderSpec:
    base_url: str
    api_key_env: str
    default_model: str
    fallback_model: str | None = None


PROVIDERS = {
    OPENROUTER: ProviderSpec("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "openrouter/free", "nex-agi/nex-n2.5-pro:free"),
    GEMINI: ProviderSpec("https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY", "gemini-2.5-flash-lite"),
    GROQ: ProviderSpec("https://api.groq.com/openai/v1", "GROQ_API_KEY", "openai/gpt-oss-20b"),
    CEREBRAS: ProviderSpec("https://api.cerebras.ai/v1", "CEREBRAS_API_KEY", "llama-3.3-70b"),
    HF_INFERENCE: ProviderSpec("https://router.huggingface.co/v1", "HF_TOKEN", "Qwen/Qwen2.5-1.5B-Instruct"),
}


def is_cloud(provider: str) -> bool:
    return provider in PROVIDERS


def _env_prefix(provider: str) -> str:
    return provider.upper().replace("-", "_")


def get_api_key(provider: str) -> str:
    key = getEnvFile(PROVIDERS[provider].api_key_env, "")
    if not key:
        raise ValueError(f"{PROVIDERS[provider].api_key_env} is not set")
    return key


def get_base_url(provider: str) -> str:
    return getEnvFile(f"{_env_prefix(provider)}_BASE_URL", PROVIDERS[provider].base_url)


def get_model(provider: str) -> str:
    return getEnvFile(f"{_env_prefix(provider)}_MODEL", PROVIDERS[provider].default_model)


def get_module_model(module: str, provider: str) -> str:
    """Model override scoped to one worker, e.g. AI_ENRICH_GROQ_MODEL."""
    return getEnvFile(f"{module}_{_env_prefix(provider)}_MODEL", PROVIDERS[provider].default_model)


def _normalize_model(item: dict) -> dict | None:
    if not isinstance(item, dict):
        return None
    model_id = str(item.get("id") or item.get("name") or item.get("model") or "").strip()
    if not model_id:
        return None
    pricing = item.get("pricing") if isinstance(item.get("pricing"), dict) else {}
    prompt = str(pricing.get("prompt", ""))
    completion = str(pricing.get("completion", ""))
    free = model_id.endswith(":free") or (prompt in ("0", "0.0") and completion in ("0", "0.0"))
    return {"id": model_id, "label": str(item.get("name") or model_id), "free": free}


def _list_ollama_models(timeout: int) -> list[dict]:
    urls = []
    primary = get_configured_ollama_url()
    if primary:
        urls.append(primary.rstrip("/"))
    for url in ollama_probe_urls():
        candidate = url.rstrip("/")
        if candidate not in urls:
            urls.append(candidate)
    for url in urls:
        try:
            response = requests.get(f"{url}/api/tags", timeout=timeout)
            response.raise_for_status()
            names = [item.get("name") for item in response.json().get("models", []) if item.get("name")]
            return sorted(({"id": name, "label": name, "free": True} for name in names[:MAX_MODELS]), key=lambda m: m["id"].lower())
        except Exception as e:
            logger.warning("ollama.models_fetch_failed", url=url, error=str(e))
    return []


def list_models(provider: str, timeout: int = 5) -> list[dict]:
    """Normalized model choices from a provider, free models first."""
    if provider == "ollama":
        return _list_ollama_models(timeout)
    if not is_cloud(provider):
        return []
    response = requests.get(
        f"{get_base_url(provider).rstrip('/')}/models",
        headers={"Authorization": f"Bearer {get_api_key(provider)}"}, timeout=timeout,
    )
    response.raise_for_status()
    items = response.json().get("data", [])
    models = [model for item in items[:MAX_MODELS] if (model := _normalize_model(item))]
    return sorted(models, key=lambda m: (not m["free"], m["id"].lower()))


def ping(provider: str, timeout: int = 5, base_url: str | None = None) -> bool:
    url = base_url or get_base_url(provider)
    try:
        resp = requests.get(
            f"{url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {get_api_key(provider)}"}, timeout=timeout,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("cloud.ping_failed", provider=provider, error=str(e))
        return False


def _payload(provider: str, model: str, messages: list[dict], json_mode: bool) -> dict:
    payload: dict = {"model": model, "messages": messages, "temperature": 0}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    if provider == OPENROUTER and (model == "openrouter/free" or model.endswith(":free")):
        payload["reasoning"] = {"enabled": False}
    return payload


def chat(provider: str, messages: list[dict], timeout: int = 90, json_mode: bool = False, model: str | None = None) -> str | None:
    """Return the first non-empty answer; a configured fallback model is tried after the primary."""
    key = get_api_key(provider)
    spec = PROVIDERS[provider]
    primary = model or get_model(provider)
    models = [primary] + ([spec.fallback_model] if spec.fallback_model and spec.fallback_model != primary else [])
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    url = f"{get_base_url(provider).rstrip('/')}/chat/completions"
    for index, model in enumerate(models):
        if index:
            logger.warning("cloud.fallback_used", provider=provider, primary=primary, fallback=model)
        for attempt, delay in enumerate((0, 1, 3)):
            if attempt:
                time.sleep(delay)
            try:
                resp = requests.post(url, headers=headers, json=_payload(provider, model, messages, json_mode), timeout=timeout)
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"].get("content")
                if content and content.strip():
                    return content.strip()
                logger.warning("cloud.empty_response", provider=provider, model=model, attempt=attempt)
            except Exception as e:
                logger.warning("cloud.error", provider=provider, model=model, attempt=attempt, error=str(e))
    return None
