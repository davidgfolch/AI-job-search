import os
import sys
import time


def _stage(msg):
    """Timestamped step marker streamed live to the console.

    pytest runs with --capture=tee-sys (apps/aiEnrich/pyproject.toml), so these
    lines reach the GitHub Actions log immediately instead of being buffered
    until the test finishes: the last line printed shows where CI hangs.
    """
    now = time.time()
    print(f"[{time.strftime('%H:%M:%S', time.localtime(now))}.{int(now % 1 * 1000):03d}] config_test {msg}", file=sys.stderr, flush=True)


_stage("module import: stdlib ok")
import pytest
from unittest.mock import patch

_stage("module import: importing commonlib.test.ollama_constants")
from commonlib.test.ollama_constants import OLLAMA_TEST_URL
_stage("module import: done")


@pytest.fixture(autouse=True)
def clean_env():
    _stage("fixture clean_env: setup")
    env_vars = [
        "AI_ENRICH_JOB",
        "AI_ENRICH_OLLAMA_BASE_URL",
        "AI_ENRICH_TIMEOUT_JOB",
    ]
    original = {k: os.environ.get(k) for k in env_vars}
    _stage("fixture clean_env: setup done, running test")
    yield
    _stage("fixture clean_env: teardown")
    for k, v in original.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    _stage("fixture clean_env: teardown done")


@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, True, id="default_true"),
    pytest.param("true", True, id="explicit_true"),
    pytest.param("false", False, id="explicit_false"),
])
def test_get_job_enabled(env_val, expected):
    _stage(f"test_get_job_enabled(env_val={env_val!r}): start")
    if env_val is None:
        os.environ.pop("AI_ENRICH_JOB", None)
    else:
        os.environ["AI_ENRICH_JOB"] = env_val
    _stage(f"test_get_job_enabled(env_val={env_val!r}): importing aiEnrich.main")
    from aiEnrich.main import get_job_enabled
    _stage(f"test_get_job_enabled(env_val={env_val!r}): calling get_job_enabled()")
    result = get_job_enabled()
    _stage(f"test_get_job_enabled(env_val={env_val!r}): got {result!r}, asserting")
    assert result is expected
    _stage(f"test_get_job_enabled(env_val={env_val!r}): done")


@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, OLLAMA_TEST_URL, id="default"),
    pytest.param("http://custom:11434", "http://custom:11434", id="custom"),
])
def test_get_ollama_base_url(env_val, expected):
    _stage(f"test_get_ollama_base_url(env_val={env_val!r}): start")
    if env_val is None:
        os.environ.pop("AI_ENRICH_OLLAMA_BASE_URL", None)
    else:
        os.environ["AI_ENRICH_OLLAMA_BASE_URL"] = env_val
    _stage(f"test_get_ollama_base_url(env_val={env_val!r}): importing aiEnrich.dataExtractor")
    from aiEnrich.dataExtractor import get_ollama_base_url
    _stage(f"test_get_ollama_base_url(env_val={env_val!r}): calling get_ollama_base_url()")
    result = get_ollama_base_url()
    _stage(f"test_get_ollama_base_url(env_val={env_val!r}): got {result!r}, asserting")
    assert result == expected
    _stage(f"test_get_ollama_base_url(env_val={env_val!r}): done")


@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, 90, id="default"),
    pytest.param("120", 120, id="custom"),
])
def test_get_timeout_job(env_val, expected):
    _stage(f"test_get_timeout_job(env_val={env_val!r}): start")
    if env_val is None:
        os.environ.pop("AI_ENRICH_TIMEOUT_JOB", None)
    else:
        os.environ["AI_ENRICH_TIMEOUT_JOB"] = env_val
    _stage(f"test_get_timeout_job(env_val={env_val!r}): importing aiEnrich.dataExtractor")
    from aiEnrich.dataExtractor import get_timeout_job
    _stage(f"test_get_timeout_job(env_val={env_val!r}): calling get_timeout_job()")
    result = get_timeout_job()
    _stage(f"test_get_timeout_job(env_val={env_val!r}): got {result!r}, asserting")
    assert result == expected
    _stage(f"test_get_timeout_job(env_val={env_val!r}): done")
