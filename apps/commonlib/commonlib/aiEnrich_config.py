from commonlib.environmentUtil import getEnv, getEnvBool
from commonlib.ollama_config import OLLAMA_DEFAULT_BASE_URL

OPENROUTER_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_DEFAULT_MODEL = "openrouter/free"
OPENROUTER_DEFAULT_FALLBACK_MODEL = "nex-agi/nex-n2.5-pro:free"


def get_job_enabled() -> bool:
    return getEnvBool("AI_ENRICH_JOB", True)


def get_ollama_base_url() -> str:
    return getEnv("AI_ENRICH_OLLAMA_BASE_URL", OLLAMA_DEFAULT_BASE_URL)


def get_timeout_job() -> int:
    return int(getEnv("AI_ENRICH_TIMEOUT_JOB", "90"))


def get_model() -> str:
    return getEnv("AI_ENRICH_OLLAMA_MODEL", "ollama/qwen2.5:3b")


def get_max_ollama_failures() -> int:
    return int(getEnv("AI_ENRICH_MAX_OLLAMA_FAILURES", "3"))


def get_backend() -> str:
    return getEnv("AI_ENRICH_BACKEND", "ollama")


def get_openrouter_base_url() -> str:
    return getEnv("AI_ENRICH_OPENROUTER_BASE_URL", OPENROUTER_DEFAULT_BASE_URL)


def get_openrouter_model() -> str:
    return getEnv("AI_ENRICH_OPENROUTER_MODEL", OPENROUTER_DEFAULT_MODEL)


def get_openrouter_fallback_model() -> str:
    return getEnv("AI_ENRICH_OPENROUTER_FALLBACK_MODEL", OPENROUTER_DEFAULT_FALLBACK_MODEL)