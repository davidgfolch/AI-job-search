import os
import pytest
from unittest.mock import patch
from aiEnrich3.config import (
    get_input_max_len,
    get_batch_size,
    get_job_enabled,
    get_skill_enabled,
)


@pytest.mark.parametrize(
    "env_val, expected",
    [
        ("5000", 5000),
        (None, 10000),
    ],
)
def test_get_input_max_len(env_val, expected):
    with patch.dict(
        os.environ, {"AI_ENRICH3_INPUT_MAX_LEN": env_val} if env_val else {}, clear=True
    ):
        assert get_input_max_len() == expected


@pytest.mark.parametrize(
    "env_val, expected",
    [
        ("2", 2),
        (None, 4),
    ],
)
def test_get_batch_size(env_val, expected):
    with patch.dict(
        os.environ,
        {"AI_ENRICH3_MAX_CONCURRENCY": env_val} if env_val else {},
        clear=True,
    ):
        assert get_batch_size() == expected


def test_get_job_enabled_default_true():
    os.environ.pop("AI_ENRICH3_JOB", None)
    assert get_job_enabled() is True


@pytest.mark.parametrize(
    "env_val, expected",
    [
        ("true", True),
        ("false", False),
        ("1", True),
        ("0", False),
        ("yes", True),
        ("no", False),
    ],
)
def test_get_job_enabled_values(env_val, expected):
    os.environ["AI_ENRICH3_JOB"] = env_val
    assert get_job_enabled() is expected


def test_get_skill_enabled_default_false():
    os.environ.pop("AI_ENRICH3_SKILL", None)
    assert get_skill_enabled() is False


@pytest.mark.parametrize(
    "env_val, expected",
    [
        ("true", True),
        ("false", False),
        ("1", True),
        ("0", False),
    ],
)
def test_get_skill_enabled_values(env_val, expected):
    os.environ["AI_ENRICH3_SKILL"] = env_val
    assert get_skill_enabled() is expected
