import os
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def clean_env():
    env_vars = [
        "AI_ENRICH_JOB",
        "AI_ENRICH_SKILL",
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


class TestConfig:
    def test_get_job_enabled_default_true(self):
        os.environ.pop("AI_ENRICH_JOB", None)
        from aiEnrich.main import get_job_enabled

        assert get_job_enabled() is True

    def test_get_job_enabled_explicit_true(self):
        os.environ["AI_ENRICH_JOB"] = "true"
        from aiEnrich.main import get_job_enabled

        assert get_job_enabled() is True

    def test_get_job_enabled_false(self):
        os.environ["AI_ENRICH_JOB"] = "false"
        from aiEnrich.main import get_job_enabled

        assert get_job_enabled() is False

    def test_get_skill_enabled_default_true(self):
        os.environ.pop("AI_ENRICH_SKILL", None)
        from aiEnrich.main import get_skill_enabled

        assert get_skill_enabled() is True

    def test_get_skill_enabled_explicit_true(self):
        os.environ["AI_ENRICH_SKILL"] = "true"
        from aiEnrich.main import get_skill_enabled

        assert get_skill_enabled() is True

    def test_get_skill_enabled_false(self):
        os.environ["AI_ENRICH_SKILL"] = "false"
        from aiEnrich.main import get_skill_enabled

        assert get_skill_enabled() is False

    def test_get_ollama_base_url_default(self):
        os.environ.pop("AI_ENRICH_OLLAMA_BASE_URL", None)
        from aiEnrich.dataExtractor import get_ollama_base_url

        assert get_ollama_base_url() == "http://localhost:11434"

    def test_get_ollama_base_url_custom(self):
        os.environ["AI_ENRICH_OLLAMA_BASE_URL"] = "http://custom:11434"
        from aiEnrich.dataExtractor import get_ollama_base_url

        assert get_ollama_base_url() == "http://custom:11434"

    def test_get_timeout_job_default(self):
        os.environ.pop("AI_ENRICH_TIMEOUT_JOB", None)
        from aiEnrich.dataExtractor import get_timeout_job

        assert get_timeout_job() == 90

    def test_get_timeout_job_custom(self):
        os.environ["AI_ENRICH_TIMEOUT_JOB"] = "120"
        from aiEnrich.dataExtractor import get_timeout_job

        assert get_timeout_job() == 120
