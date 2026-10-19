import os
import pytest
from unittest.mock import patch, MagicMock
from contextlib import contextmanager

from .. import dataExtractor as dataExtractor_module
from .. import ollama_backend as ollama_backend_module


@pytest.fixture
def mock_deps():
    with patch('aiEnrich.dataExtractor.MysqlUtil') as mysql_util, \
         patch('aiEnrich.dataExtractor._save') as save_chk, \
         patch('aiEnrich.dataExtractor.footer') as footer_chk, patch('aiEnrich.dataExtractor.StopWatch'), \
         patch('aiEnrich.dataExtractor.mapJob'), \
         patch('aiEnrich.dataExtractor.AiEnrichRepository') as repo_cls, \
         patch('aiEnrich.dataExtractor.ping_backend', return_value=True), \
         patch('aiEnrich.dataExtractor.get_backend', return_value='ollama'), \
         patch('aiEnrich.ollama_backend.query_ollama') as mock_ollama, \
         patch('aiEnrich.ollama_backend.ping_backend', return_value=True) as mock_ping, \
         patch('aiEnrich.ollama_backend.get_backend', return_value='ollama'):
        mysql = MagicMock()
        mysql_util.return_value.__enter__.return_value = mysql
        repo = MagicMock()
        repo.count_pending_enrichment.return_value = 0
        repo_cls.return_value = repo
        dataExtractor_module.totalCount = 0
        dataExtractor_module.jobErrors = set()
        ollama_backend_module._resolved_ollama_url = None
        ollama_backend_module._ollama_server_known = False
        ollama_backend_module.ollama_consecutive_failures = 0
        yield {'mysql': mysql, 'save': save_chk, 'repo': repo, 'ollama': mock_ollama, 'ping': mock_ping, 'footer': footer_chk}
        ollama_backend_module._resolved_ollama_url = None
        ollama_backend_module._ollama_server_known = False
        ollama_backend_module.ollama_consecutive_failures = 0


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
