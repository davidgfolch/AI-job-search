import os
import pytest
from unittest.mock import MagicMock

from aiEnrich import aiEnrich_config
from aiEnrich.aiEnrich_config import (
    OPENROUTER_DEFAULT_BASE_URL, OPENROUTER_DEFAULT_MODEL, OPENROUTER_DEFAULT_FALLBACK_MODEL,
    get_job_enabled, get_ollama_base_url, get_timeout_job, get_model, get_max_ollama_failures,
    get_max_validation_retries, get_backend, get_openrouter_base_url, get_openrouter_model,
    get_openrouter_fallback_model, get_backend_url,
)

CONFIG_ENV_VARS = [
    "AI_ENRICH_BACKEND", "AI_ENRICH_OPENROUTER_BASE_URL", "AI_ENRICH_OPENROUTER_MODEL",
    "AI_ENRICH_OPENROUTER_FALLBACK_MODEL", "AI_ENRICH_OLLAMA_BASE_URL", "AI_ENRICH_OLLAMA_MODEL",
    "AI_ENRICH_MAX_OLLAMA_FAILURES", "AI_ENRICH_MAX_VALIDATION_RETRIES", "AI_ENRICH_TIMEOUT_JOB", "AI_ENRICH_JOB",
    "AI_ENRICH_BACKEND_URL",
]


@pytest.fixture(autouse=True)
def clean_env():
    original = {k: os.environ.get(k) for k in CONFIG_ENV_VARS}
    aiEnrich_config._BACKEND_URL_CACHE = None
    yield
    aiEnrich_config._BACKEND_URL_CACHE = None
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
    assert get_timeout_job() == 300
    assert get_model() == "ollama/qwen2.5:3b"
    assert get_max_ollama_failures() == 3
    assert get_max_validation_retries() == 1


def test_get_backend_url_prefers_configured_env(monkeypatch):
    monkeypatch.setenv("AI_ENRICH_BACKEND_URL", "http://configured:8000")
    probe = MagicMock(return_value=False)
    monkeypatch.setattr(aiEnrich_config, "_probe_backend_url", probe)

    assert get_backend_url() == "http://configured:8000"
    probe.assert_not_called()


def test_get_backend_url_probes_candidates_in_order(monkeypatch):
    monkeypatch.delenv("AI_ENRICH_BACKEND_URL", raising=False)
    probed = []

    def fake_probe(url, timeout=2.0):
        probed.append(url)
        return url == "http://host.docker.internal:8000"

    monkeypatch.setattr(aiEnrich_config, "_probe_backend_url", fake_probe)

    assert get_backend_url() == "http://host.docker.internal:8000"
    assert probed == ["http://backend:8000", "http://host.docker.internal:8000"]


def test_get_backend_url_falls_back_to_host_and_caches(monkeypatch):
    monkeypatch.delenv("AI_ENRICH_BACKEND_URL", raising=False)
    probed = []

    def fake_probe(url, timeout=2.0):
        probed.append(url)
        return False

    monkeypatch.setattr(aiEnrich_config, "_probe_backend_url", fake_probe)

    assert get_backend_url() == "http://localhost:8000"
    assert len(probed) == 3
    assert get_backend_url() == "http://localhost:8000"
    assert len(probed) == 3
