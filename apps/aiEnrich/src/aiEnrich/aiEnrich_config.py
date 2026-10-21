import requests

from commonlib.environmentUtil import getEnv, getEnvBool
from commonlib.ollama_config import (
    BACKEND_HOST_BASE_URL,
    OLLAMA_HOST_BASE_URL,
    backend_candidate_urls,
)

OPENROUTER_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_DEFAULT_MODEL = "openrouter/free"
OPENROUTER_DEFAULT_FALLBACK_MODEL = "nex-agi/nex-n2.5-pro:free"

_BACKEND_URL_CACHE: str | None = None


def _probe_backend_url(url: str, timeout: float = 2.0) -> bool:
    """Return True when the backend answers /health at `url`."""
    try:
        return requests.get(f"{url.rstrip('/')}/health", timeout=timeout).ok
    except Exception:
        return False


def get_job_enabled() -> bool:
    return getEnvBool("AI_ENRICH_JOB", True)


def get_ollama_base_url() -> str:
    return getEnv("AI_ENRICH_OLLAMA_BASE_URL", OLLAMA_HOST_BASE_URL)


def get_timeout_job() -> int:
    return int(getEnv("AI_ENRICH_TIMEOUT_JOB", "90"))


def get_model() -> str:
    return getEnv("AI_ENRICH_OLLAMA_MODEL", "ollama/qwen2.5:3b")


def get_max_ollama_failures() -> int:
    return int(getEnv("AI_ENRICH_MAX_OLLAMA_FAILURES", "3"))


def get_max_validation_retries() -> int:
    return int(getEnv("AI_ENRICH_MAX_VALIDATION_RETRIES", "1"))


def get_backend() -> str:
    return getEnv("AI_ENRICH_BACKEND", "ollama")


def get_backend_url() -> str:
    """Base URL of the FastAPI backend used to notify the watcher matcher.

    Honors `AI_ENRICH_BACKEND_URL` when set; otherwise probes the shared backend
    candidate URLs (Docker service -> host via Docker -> host) and caches the
    first reachable one, so enrichment workers reach the backend whether running
    on the host or inside Docker Compose without any env changes.
    """
    global _BACKEND_URL_CACHE
    if _BACKEND_URL_CACHE is not None:
        return _BACKEND_URL_CACHE
    configured = getEnv("AI_ENRICH_BACKEND_URL")
    if configured:
        _BACKEND_URL_CACHE = configured
        return _BACKEND_URL_CACHE
    for url in backend_candidate_urls():
        if _probe_backend_url(url):
            _BACKEND_URL_CACHE = url
            return _BACKEND_URL_CACHE
    _BACKEND_URL_CACHE = BACKEND_HOST_BASE_URL
    return _BACKEND_URL_CACHE


def get_openrouter_base_url() -> str:
    return getEnv("AI_ENRICH_OPENROUTER_BASE_URL", OPENROUTER_DEFAULT_BASE_URL)


def get_openrouter_model() -> str:
    return getEnv("AI_ENRICH_OPENROUTER_MODEL", OPENROUTER_DEFAULT_MODEL)


def get_openrouter_fallback_model() -> str:
    return getEnv("AI_ENRICH_OPENROUTER_FALLBACK_MODEL", OPENROUTER_DEFAULT_FALLBACK_MODEL)