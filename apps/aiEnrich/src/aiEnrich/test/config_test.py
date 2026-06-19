import os
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def clean_env():
    env_vars = [
        "AI_ENRICH_JOB",
        "AI_ENRICH_OLLAMA_BASE_URL",
        "AI_ENRICH_TIMEOUT_JOB",
    ]
    original = {k: os.environ.get(k) for k in env_vars}
    yield
    for k, v in original.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, True, id="default_true"),
    pytest.param("true", True, id="explicit_true"),
    pytest.param("false", False, id="explicit_false"),
])
def test_get_job_enabled(env_val, expected):
    if env_val is None:
        os.environ.pop("AI_ENRICH_JOB", None)
    else:
        os.environ["AI_ENRICH_JOB"] = env_val
    from aiEnrich.main import get_job_enabled
    assert get_job_enabled() is expected


@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, "http://localhost:11434", id="default"),
    pytest.param("http://custom:11434", "http://custom:11434", id="custom"),
])
def test_get_ollama_base_url(env_val, expected):
    if env_val is None:
        os.environ.pop("AI_ENRICH_OLLAMA_BASE_URL", None)
    else:
        os.environ["AI_ENRICH_OLLAMA_BASE_URL"] = env_val
    from aiEnrich.dataExtractor import get_ollama_base_url
    assert get_ollama_base_url() == expected


@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, 90, id="default"),
    pytest.param("120", 120, id="custom"),
])
def test_get_timeout_job(env_val, expected):
    if env_val is None:
        os.environ.pop("AI_ENRICH_TIMEOUT_JOB", None)
    else:
        os.environ["AI_ENRICH_TIMEOUT_JOB"] = env_val
    from aiEnrich.dataExtractor import get_timeout_job
    assert get_timeout_job() == expected
