import os
import pytest
from commonlib.aiEnrich_config import (
    OPENROUTER_DEFAULT_BASE_URL, OPENROUTER_DEFAULT_MODEL, OPENROUTER_DEFAULT_FALLBACK_MODEL,
    get_job_enabled, get_ollama_base_url, get_timeout_job, get_model, get_max_ollama_failures,
    get_backend, get_openrouter_base_url, get_openrouter_model, get_openrouter_fallback_model,
)

CONFIG_ENV_VARS = [
    "AI_ENRICH_BACKEND", "AI_ENRICH_OPENROUTER_BASE_URL", "AI_ENRICH_OPENROUTER_MODEL",
    "AI_ENRICH_OPENROUTER_FALLBACK_MODEL", "AI_ENRICH_OLLAMA_BASE_URL", "AI_ENRICH_OLLAMA_MODEL",
    "AI_ENRICH_MAX_OLLAMA_FAILURES", "AI_ENRICH_TIMEOUT_JOB", "AI_ENRICH_JOB",
]


@pytest.fixture(autouse=True)
def clean_env():
    original = {k: os.environ.get(k) for k in CONFIG_ENV_VARS}
    yield
    for k, v in original.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_openrouter_default_constants():
    assert OPENROUTER_DEFAULT_BASE_URL == "https://openrouter.ai/api/v1"
    assert OPENROUTER_DEFAULT_MODEL == "openrouter/free"
    assert OPENROUTER_DEFAULT_FALLBACK_MODEL == "nex-agi/nex-n2.5-pro:free"


@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, "ollama", id="default_ollama"),
    pytest.param("openrouter", "openrouter", id="explicit_openrouter"),
    pytest.param("ollama", "ollama", id="explicit_ollama"),
])
def test_get_backend(env_val, expected):
    _set_or_unset("AI_ENRICH_BACKEND", env_val)
    assert get_backend() == expected


@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, "https://openrouter.ai/api/v1", id="default"),
    pytest.param("http://custom:11434", "http://custom:11434", id="custom"),
])
def test_get_openrouter_base_url(env_val, expected):
    _set_or_unset("AI_ENRICH_OPENROUTER_BASE_URL", env_val)
    assert get_openrouter_base_url() == expected


@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, "openrouter/free", id="default"),
    pytest.param("anthropic/claude-3.5-sonnet", "anthropic/claude-3.5-sonnet", id="custom"),
])
def test_get_openrouter_model(env_val, expected):
    _set_or_unset("AI_ENRICH_OPENROUTER_MODEL", env_val)
    assert get_openrouter_model() == expected


@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, "nex-agi/nex-n2.5-pro:free", id="default"),
    pytest.param("openai/gpt-4o-mini", "openai/gpt-4o-mini", id="custom"),
])
def test_get_openrouter_fallback_model(env_val, expected):
    _set_or_unset("AI_ENRICH_OPENROUTER_FALLBACK_MODEL", env_val)
    assert get_openrouter_fallback_model() == expected


def _set_or_unset(key: str, value):
    if value is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = value


def test_other_getters_defaults():
    assert get_job_enabled() is True
    assert get_ollama_base_url() == "http://localhost:11434"
    assert get_timeout_job() == 90
    assert get_model() == "ollama/qwen2.5:3b"
    assert get_max_ollama_failures() == 3