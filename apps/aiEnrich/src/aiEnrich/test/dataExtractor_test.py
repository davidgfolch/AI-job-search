import os
import pytest
from contextlib import contextmanager
from unittest.mock import patch, MagicMock

from commonlib.ollama_client import OllamaResponse
from .. import dataExtractor as dataExtractor_module
from ..dataExtractor import dataExtractor, _save, _getJobIdsList

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

        # `totalCount` and `jobErrors` are module globals that survive between calls, so the
        # footer assertions of one test would otherwise read another test's leftovers.
        dataExtractor_module.totalCount = 0
        dataExtractor_module.jobErrors = set()
        yield {'mysql': mysql, 'save': save_chk, 'repo': repo, 'ollama': mock_ollama, 'ping': mock_ping, 'footer': footer_chk}

@pytest.fixture(autouse=True)
def clean_env():
    env_vars = ["AI_ENRICH_BACKEND", "AI_ENRICH_OPENROUTER_BASE_URL", "AI_ENRICH_OPENROUTER_MODEL", "AI_ENRICH_OPENROUTER_FALLBACK_MODEL", "AI_ENRICH_MAX_VALIDATION_RETRIES"]
    original = {k: os.environ.get(k) for k in env_vars}
    yield
    for k, v in original.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

class TestDataExtractor:

    @patch('aiEnrich.dataExtractor._getJobIdsList', return_value=[1])
    def test_extractor_success(self, mock_ids, mock_deps):
        """Test success"""
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = (1, 'Job', 'Desc', 'Comp')

        with patch('aiEnrich.dataExtractor.mapJob', return_value=('Job', 'Comp', 'Desc')):
            mock_deps['ollama'].return_value = '{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": "REMOTE"}'
            assert dataExtractor() == 1
            mock_deps['save'].assert_called()
            mock_deps['ollama'].assert_called_once()

    @patch('aiEnrich.dataExtractor._getJobIdsList', return_value=[1])
    def test_skips_when_ollama_down(self, mock_ids, mock_deps):
        """Returns -1 when Ollama is unreachable"""
        mock_deps['ping'].return_value = False
        mock_deps['repo'].count_pending_enrichment.return_value = 1

        assert dataExtractor() == -1
        mock_deps['ollama'].assert_not_called()
        mock_deps['save'].assert_not_called()

    @patch('aiEnrich.dataExtractor._getJobIdsList', return_value=[1])
    def test_skips_job_when_ollama_returns_none(self, mock_ids, mock_deps):
        """Skips job without saving/erroring when ollama returns None mid-batch"""
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = (1, 'Job', 'Desc', 'Comp')
        mock_deps['ollama'].return_value = None

        with patch('aiEnrich.dataExtractor.mapJob', return_value=('Job', 'Comp', 'Desc')):
            assert dataExtractor() == 1
            mock_deps['save'].assert_not_called()
            mock_deps['ollama'].assert_called_once()

    def test_save(self, mock_deps):
        """Test save"""
        repo = MagicMock()
        with patch('aiEnrich.dataExtractor.validateResult'):
            _save(repo, 1, {'salary': '100k', 'required_technologies': 'T', 'optional_technologies': 'O', 'modality': 'REMOTE'})
            repo.update_enrichment.assert_called_once_with(1, '100k', 'T', 'O', 'REMOTE')

    @patch('aiEnrich.dataExtractor._getJobIdsList', return_value=[1, 2])
    def test_job_started_index_is_one_based(self, mock_ids, mock_deps):
        """`job.started` counts from 1 so it agrees with `processed` in the footer."""
        mock_deps['repo'].count_pending_enrichment.return_value = 2
        mock_deps['repo'].get_job_to_enrich.return_value = (1, 'Job', 'Desc', 'Comp')

        with patch('aiEnrich.dataExtractor.mapJob', return_value=('Job', 'Comp', 'Desc')), \
             patch('aiEnrich.dataExtractor.logger') as mock_logger:
            mock_deps['ollama'].return_value = '{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": "REMOTE"}'
            assert dataExtractor() == 2

        started = [c.kwargs for c in mock_logger.info.call_args_list if c.args and c.args[0] == "job.started"]
        assert [entry['index'] for entry in started] == [1, 2]

    @patch('aiEnrich.dataExtractor._getJobIdsList', return_value=[1])
    def test_footer_receives_batch_elapsed(self, mock_ids, mock_deps):
        """The footer gets the batch elapsed time so it can report media per job."""
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = (1, 'Job', 'Desc', 'Comp')

        with patch('aiEnrich.dataExtractor.mapJob', return_value=('Job', 'Comp', 'Desc')):
            mock_deps['ollama'].return_value = '{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": "REMOTE"}'
            assert dataExtractor() == 1

        assert mock_deps['footer'].call_count == 1
        args = mock_deps['footer'].call_args.args
        assert args[:3] == (1, 0, 1)
        assert args[4] >= 0

    @patch('aiEnrich.dataExtractor._getJobIdsList', return_value=[1])
    def test_job_work_runs_inside_the_job_context(self, mock_ids, mock_deps):
        """Saving must happen inside the context, or its `db.updated` record has no `job_id`."""
        order = []
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = (1, 'Job', 'Desc', 'Comp')

        @contextmanager
        def spy(job_id):
            order.append(('enter', job_id))
            yield
            order.append(('exit', job_id))

        mock_deps['save'].side_effect = lambda *a, **k: order.append(('save', None))

        with patch('aiEnrich.dataExtractor.mapJob', return_value=('Job', 'Comp', 'Desc')), \
             patch('aiEnrich.dataExtractor.job_log_context', spy):
            mock_deps['ollama'].return_value = '{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": "REMOTE"}'
            assert dataExtractor() == 1

        assert order[0] == ('enter', 1)
        assert ('save', None) in order
        assert order.index(('save', None)) < order.index(('exit', 1))


@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, "ollama", id="default_ollama"),
    pytest.param("openrouter", "openrouter", id="explicit_openrouter"),
    pytest.param("ollama", "ollama", id="explicit_ollama"),
])
def test_get_backend(env_val, expected):
    if env_val is None:
        os.environ.pop("AI_ENRICH_BACKEND", None)
    else:
        os.environ["AI_ENRICH_BACKEND"] = env_val
    from aiEnrich.dataExtractor import get_backend
    assert get_backend() == expected

@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, "https://openrouter.ai/api/v1", id="default"),
    pytest.param("http://custom:11434", "http://custom:11434", id="custom"),
])
def test_get_openrouter_base_url(env_val, expected):
    if env_val is None:
        os.environ.pop("AI_ENRICH_OPENROUTER_BASE_URL", None)
    else:
        os.environ["AI_ENRICH_OPENROUTER_BASE_URL"] = env_val
    from aiEnrich.dataExtractor import get_openrouter_base_url
    assert get_openrouter_base_url() == expected

@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, "openrouter/free", id="default"),
    pytest.param("anthropic/claude-3.5-sonnet", "anthropic/claude-3.5-sonnet", id="custom"),
])
def test_get_openrouter_model(env_val, expected):
    if env_val is None:
        os.environ.pop("AI_ENRICH_OPENROUTER_MODEL", None)
    else:
        os.environ["AI_ENRICH_OPENROUTER_MODEL"] = env_val
    from aiEnrich.dataExtractor import get_openrouter_model
    assert get_openrouter_model() == expected

@pytest.mark.parametrize("env_val, expected", [
    pytest.param(None, "nex-agi/nex-n2.5-pro:free", id="default"),
    pytest.param("openai/gpt-4o-mini", "openai/gpt-4o-mini", id="custom"),
])
def test_get_openrouter_fallback_model(env_val, expected):
    if env_val is None:
        os.environ.pop("AI_ENRICH_OPENROUTER_FALLBACK_MODEL", None)
    else:
        os.environ["AI_ENRICH_OPENROUTER_FALLBACK_MODEL"] = env_val
    from aiEnrich.dataExtractor import get_openrouter_fallback_model
    assert get_openrouter_fallback_model() == expected


class TestPingBackend:
    def test_routes_to_ollama(self):
        os.environ["AI_ENRICH_BACKEND"] = "ollama"
        from aiEnrich import dataExtractor
        with patch.object(dataExtractor, "resolve_ollama_url", return_value="http://host:11434") as mock_resolve, \
             patch.object(dataExtractor, "ping_openrouter") as mock_ping_or:
            assert dataExtractor.ping_backend() is True
        mock_resolve.assert_called_once()
        mock_ping_or.assert_not_called()

    def test_routes_to_openrouter(self):
        os.environ["AI_ENRICH_BACKEND"] = "openrouter"
        from aiEnrich import dataExtractor
        with patch.object(dataExtractor, "resolve_ollama_url", return_value=None) as mock_resolve, \
             patch.object(dataExtractor, "ping_openrouter", return_value=True) as mock_ping_or:
            assert dataExtractor.ping_backend() is True
        mock_ping_or.assert_called_once()
        mock_resolve.assert_not_called()


class TestProcessJobSafeBackend:
    def test_uses_openrouter_when_backend_openrouter(self):
        os.environ["AI_ENRICH_BACKEND"] = "openrouter"
        from aiEnrich.dataExtractor import _process_job_safe
        repo = MagicMock()
        repo.get_job_to_enrich.return_value = (1, "Job", "Desc", "Comp")
        with patch("aiEnrich.dataExtractor.mapJob", return_value=("Job", "Comp", "Desc")), \
             patch("aiEnrich.dataExtractor.query_openrouter", return_value='{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": "REMOTE"}') as mock_or, \
             patch("aiEnrich.dataExtractor.query_ollama") as mock_ollama, \
             patch("aiEnrich.dataExtractor._save") as mock_save, \
             patch("aiEnrich.dataExtractor.validateResult"), \
             patch("aiEnrich.dataExtractor.footer"), \
             patch("aiEnrich.dataExtractor.stopWatch"):
            _process_job_safe(repo, 1, 1, 0, "enrich")
        mock_or.assert_called_once()
        mock_ollama.assert_not_called()
        mock_save.assert_called_once()

    def test_uses_ollama_when_backend_ollama(self):
        os.environ["AI_ENRICH_BACKEND"] = "ollama"
        from aiEnrich.dataExtractor import _process_job_safe
        repo = MagicMock()
        repo.get_job_to_enrich.return_value = (1, "Job", "Desc", "Comp")
        response = OllamaResponse(
            text='{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": "REMOTE"}',
            url="http://ollama", done=True, done_reason="stop",
        )
        with patch("aiEnrich.dataExtractor.mapJob", return_value=("Job", "Comp", "Desc")), \
             patch("aiEnrich.dataExtractor.query_openrouter") as mock_or, \
             patch("aiEnrich.dataExtractor.query_ollama", return_value=response) as mock_ollama, \
             patch("aiEnrich.dataExtractor._save") as mock_save, \
             patch("aiEnrich.dataExtractor.validateResult"), \
             patch("aiEnrich.dataExtractor.footer"), \
             patch("aiEnrich.dataExtractor.stopWatch"):
            _process_job_safe(repo, 1, 1, 0, "enrich")
        mock_ollama.assert_called_once()
        assert mock_ollama.call_args.kwargs["return_metadata"] is True
        assert mock_ollama.call_args.kwargs["response_schema"]["required"] == [
            "required_technologies", "optional_technologies", "salary", "modality",
        ]
        mock_or.assert_not_called()
        mock_save.assert_called_once()
