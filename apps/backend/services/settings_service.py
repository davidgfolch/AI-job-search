import time

from commonlib.cloud_llm import get_base_url, is_cloud, list_models
from commonlib.environmentUtil import getEnv, getEnvAll, setEnv
from commonlib.observability import get_logger
from commonlib.ollama_config import get_configured_ollama_url
from repositories.scrapper_state_repository import ScrapperStateRepository

logger = get_logger("backend.services.settings_service")

_repo = ScrapperStateRepository()
_models_cache: dict[str, tuple[float, dict]] = {}


def _empty_models(provider: str) -> dict:
    return {"provider": provider, "models": [], "source": "fallback", "cached": False, "fetched_at": None}


def get_provider_models(provider: str, refresh: bool = False) -> dict:
    if provider != "ollama" and not is_cloud(provider):
        return _empty_models(provider)
    base = (get_configured_ollama_url() or "ollama") if provider == "ollama" else get_base_url(provider)
    cache_key = f"{provider}:{base}"
    ttl = int(getEnv("LLM_MODELS_CACHE_TTL_SECONDS", "604800"))
    cached = _models_cache.get(cache_key)
    if cached and not refresh and time.time() - cached[0] < ttl:
        return {**cached[1], "cached": True}
    try:
        models = list_models(provider)
    except Exception as e:
        logger.warning("provider.models_fetch_failed", provider=provider, error=str(e))
        return _empty_models(provider)
    if not models:
        return _empty_models(provider)
    fetched_at = time.time()
    payload = {"provider": provider, "models": models, "source": "live", "cached": False, "fetched_at": fetched_at}
    _models_cache[cache_key] = (fetched_at, payload)
    return payload

def get_env_settings() -> dict[str, str]:
    return getEnvAll()

def update_env_setting(key: str, value: str) -> dict[str, str]:
    setEnv(key, value)
    logger.info("settings.updated", key=key, count=1)
    return getEnvAll()

def update_env_settings_bulk(updates: dict[str, str]) -> dict[str, str]:
    from commonlib.environmentUtil import setEnvBulk
    setEnvBulk(updates)
    logger.info("settings.updated", count=len(updates))
    return getEnvAll()

def get_scrapper_state() -> dict:
    try:
        return _repo.get_all()
    except Exception as e:
        logger.exception("scrapper_state.read_failed", error=str(e))
        return {}

def update_scrapper_state(state: dict) -> dict:
    try:
        return _repo.replace_all(state)
    except Exception as e:
        logger.exception("scrapper_state.write_failed", error=str(e))
        return state
