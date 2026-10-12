import os
import pytest
from unittest.mock import patch, MagicMock
from contextlib import contextmanager

from .. import dataExtractor as dataExtractor_module


@pytest.fixture
def mock_deps():
    with patch('aiEnrich.dataExtractor.MysqlUtil') as mysql_util, \
         patch('aiEnrich.dataExtractor._save') as save_chk, \
         patch('aiEnrich.dataExtractor.footer') as footer_chk, patch('aiEnrich.dataExtractor.StopWatch'), \
         patch('aiEnrich.dataExtractor.mapJob'), \
         patch('aiEnrich.dataExtractor.AiEnrichRepository') as repo_cls, \
         patch('aiEnrich.dataExtractor.query_ollama') as mock_ollama, \
         patch('aiEnrich.dataExtractor.ping_backend', return_value=True) as mock_ping, \
         patch('aiEnrich.dataExtractor.get_backend', return_value='ollama'):
        mysql = MagicMock()
        mysql_util.return_value.__enter__.return_value = mysql
        repo = MagicMock()
        repo_cls.return_value = repo
        dataExtractor_module.totalCount = 0
        dataExtractor_module.jobErrors = set()
        yield {'mysql': mysql, 'save': save_chk, 'repo': repo, 'ollama': mock_ollama, 'ping': mock_ping, 'footer': footer_chk}


@pytest.fixture(autouse=True)
def clean_env():
    env_vars = [
        "AI_ENRICH_BACKEND", "AI_ENRICH_OPENROUTER_BASE_URL", "AI_ENRICH_OPENROUTER_MODEL",
        "AI_ENRICH_OPENROUTER_FALLBACK_MODEL", "AI_ENRICH_MAX_VALIDATION_RETRIES",
    ]
    original = {k: os.environ.get(k) for k in env_vars}
    yield
    for k, v in original.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


ENV_GET_PARAMS = [
    pytest.param(None, "ollama", id="default_ollama"),
    pytest.param("openrouter", "openrouter", id="explicit_openrouter"),
    pytest.param("ollama", "ollama", id="explicit_ollama"),
]
OPENROUTER_URL_PARAMS = [
    pytest.param(None, "https://openrouter.ai/api/v1", id="default"),
    pytest.param("http://custom:11434", "http://custom:11434", id="custom"),
]
OPENROUTER_MODEL_PARAMS = [
    pytest.param(None, "openrouter/free", id="default"),
    pytest.param("anthropic/claude-3.5-sonnet", "anthropic/claude-3.5-sonnet", id="custom"),
]
OPENROUTER_FALLBACK_PARAMS = [
    pytest.param(None, "nex-agi/nex-n2.5-pro:free", id="default"),
    pytest.param("openai/gpt-4o-mini", "openai/gpt-4o-mini", id="custom"),
]
