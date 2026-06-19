import os
import pytest
from unittest.mock import patch
from ..config import (
    get_job_system_prompt,
    get_batch_size,
    get_input_max_len,
    get_enrich_timeout_job,
    should_cleanup_gpu,
    get_job_enabled,
)


def test_get_job_system_prompt():
    prompt = get_job_system_prompt()
    assert "You are an expert at analyzing job offers" in prompt
    assert "required_technologies" in prompt


@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, True, id="default_true"),
    pytest.param("true", True, id="explicit_true"),
    pytest.param("false", False, id="explicit_false"),
])
def test_get_job_enabled(env_val, expected):
    if env_val is None:
        os.environ.pop("AI_ENRICHNEW_JOB", None)
    else:
        os.environ["AI_ENRICHNEW_JOB"] = env_val
    from aiEnrichNew.config import get_job_enabled as fn
    assert fn() is expected


@pytest.mark.parametrize("return_val, expected", [
    pytest.param("10", 10, id="default"),
    pytest.param("50", 50, id="custom"),
])
@patch("aiEnrichNew.config.getEnv")
def test_get_batch_size(mock_get_env, return_val, expected):
    mock_get_env.return_value = return_val
    assert get_batch_size() == expected


@patch("aiEnrichNew.config.getEnv")
def test_get_input_max_len(mock_get_env):
    mock_get_env.return_value = "5000"
    assert get_input_max_len() == 5000


@patch("aiEnrichNew.config.getEnv")
def test_get_enrich_timeout_job(mock_get_env):
    mock_get_env.return_value = "120.5"
    assert get_enrich_timeout_job() == 120.5


@pytest.mark.parametrize("return_val, expected", [
    pytest.param("True", True, id="true"),
    pytest.param("False", False, id="false"),
])
@patch("aiEnrichNew.config.getEnv")
def test_should_cleanup_gpu(mock_get_env, return_val, expected):
    mock_get_env.return_value = return_val
    assert should_cleanup_gpu() is expected
