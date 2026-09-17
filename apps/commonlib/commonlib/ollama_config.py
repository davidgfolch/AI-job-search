"""Centralized Ollama server URL configuration and fallback ordering.

Single source of truth for the Ollama server URLs used across all modules.
Runtime override is done via the dedicated env var per module (e.g.
`AI_ENRICH_OLLAMA_BASE_URL`), whose default falls back to the constants below.
`ollama_candidate_urls` provides the ordered fallback chain used when the
primary URL is unreachable (containerized service -> host via Docker -> host).
"""
from commonlib.environmentUtil import getEnv

OLLAMA_HOST_BASE_URL = "http://localhost:11434"
OLLAMA_DOCKER_BASE_URL = "http://ollama:11434"
OLLAMA_HOST_FROM_DOCKER_BASE_URL = "http://host.docker.internal:11434"

_MODULE_OLLAMA_URL_ENVS = (
    "AI_ENRICH_OLLAMA_BASE_URL",
    "AI_ENRICHSKILL_OLLAMA_BASE_URL",
    "OLLAMA_BASE_URL",
)

MAX_NEW_TOKENS_ENVS = ("AI_ENRICH_MAX_NEW_TOKENS", "AI_ENRICHSKILL_MAX_NEW_TOKENS")
NUM_CTX_ENVS = ("AI_ENRICH_NUM_CTX", "AI_ENRICHSKILL_NUM_CTX")
REPEAT_PENALTY_ENVS = ("AI_ENRICH_REPEAT_PENALTY", "AI_ENRICHSKILL_REPEAT_PENALTY")
DEFAULT_REPEAT_PENALTY = 1.3
MAX_NUM_CTX = 32768


def ollama_candidate_urls(primary: str | None = None) -> tuple[str, ...]:
    """Ordered, deduplicated URLs to try, primary first and then the shared fallback chain."""
    urls = [primary] if primary else []
    for url in (OLLAMA_HOST_FROM_DOCKER_BASE_URL, OLLAMA_HOST_BASE_URL, OLLAMA_DOCKER_BASE_URL):
        if url not in urls:
            urls.append(url)
    return tuple(urls)


def ollama_probe_urls() -> tuple[str, ...]:
    """Every plausible Ollama server for liveness checks, deduplicated.

    Expands each configured module URL (via `getEnv`) through
    `ollama_candidate_urls`, then appends the shared fallback set for
    environments where no module URL is set (e.g. the backend container).
    """
    urls = []
    for env_var in _MODULE_OLLAMA_URL_ENVS:
        primary = getEnv(env_var)
        if primary:
            for url in ollama_candidate_urls(primary):
                if url not in urls:
                    urls.append(url)
    for url in (OLLAMA_HOST_FROM_DOCKER_BASE_URL, OLLAMA_HOST_BASE_URL, OLLAMA_DOCKER_BASE_URL):
        if url not in urls:
            urls.append(url)
    return tuple(urls)


def get_num_predict() -> int:
    for env in MAX_NEW_TOKENS_ENVS:
        value = getEnv(env)
        if value:
            return int(value)
    return 2048


def get_num_ctx(prompt: str, num_predict: int) -> int:
    for env in NUM_CTX_ENVS:
        value = getEnv(env)
        if value:
            return min(int(value), MAX_NUM_CTX)
    required = len(prompt) // 3 + num_predict
    bucketed = max(2048, ((required + 2047) // 2048) * 2048)
    return min(bucketed, MAX_NUM_CTX)


def get_repeat_penalty() -> float:
    for env in REPEAT_PENALTY_ENVS:
        value = getEnv(env)
        if value:
            return float(value)
    return DEFAULT_REPEAT_PENALTY


def strip_provider_prefix(model: str) -> str:
    if "/" in model:
        return model.split("/", 1)[1]
    return model