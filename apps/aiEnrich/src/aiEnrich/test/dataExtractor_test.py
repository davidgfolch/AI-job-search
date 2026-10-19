import os
import pytest
from contextlib import contextmanager
from unittest.mock import patch, MagicMock

from commonlib.ollama_client import OllamaResponse
from ..dataExtractor import dataExtractor, _save

from .dataExtractor_fixtures import (
    mock_deps, clean_env,
    ENV_GET_PARAMS, OPENROUTER_URL_PARAMS,
    OPENROUTER_MODEL_PARAMS, OPENROUTER_FALLBACK_PARAMS,
)  # noqa: F401


class TestDataExtractor:
    @patch('aiEnrich.dataExtractor._getJobBatches', return_value=[[1]])
    def test_extractor_success(self, mock_ids, mock_deps):
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = (1, 'Job', 'Desc', 'Comp')
        with patch('aiEnrich.dataExtractor.mapJob', return_value=('Job', 'Comp', 'Desc')):
            mock_deps['ollama'].return_value = '{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": "REMOTE"}'
            assert dataExtractor() == 1
            mock_deps['save'].assert_called()
            mock_deps['ollama'].assert_called_once()

    @patch('aiEnrich.dataExtractor._getJobBatches', return_value=[[1]])
    def test_skips_when_ollama_down(self, mock_ids, mock_deps):
        mock_deps['ping'].return_value = False
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        assert dataExtractor() == -1
        mock_deps['ollama'].assert_not_called()
        mock_deps['save'].assert_not_called()

    @patch('aiEnrich.dataExtractor._getJobBatches', return_value=[[1]])
    def test_retries_job_when_ollama_returns_none(self, mock_ids, mock_deps):
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = (1, 'Job', 'Desc', 'Comp')
        mock_deps['ollama'].side_effect = [None, '{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": "REMOTE"}']
        with patch('aiEnrich.dataExtractor.mapJob', return_value=('Job', 'Comp', 'Desc')):
            assert dataExtractor() == 1
            mock_deps['save'].assert_called_once()
            assert mock_deps['ollama'].call_count == 2

    def test_save(self, mock_deps):
        repo = MagicMock()
        with patch('aiEnrich.dataExtractor.validateResult'):
            _save(repo, 1, {'salary': '100k', 'required_technologies': 'T', 'optional_technologies': 'O', 'modality': 'REMOTE'})
            repo.update_enrichment.assert_called_once_with(1, '100k', 'T', 'O', 'REMOTE')

    @patch('aiEnrich.dataExtractor._getJobBatches', return_value=[[1, 2]])
    def test_job_started_index_is_one_based(self, mock_ids, mock_deps):
        mock_deps['repo'].count_pending_enrichment.return_value = 2
        mock_deps['repo'].get_job_to_enrich.return_value = (1, 'Job', 'Desc', 'Comp')
        with patch('aiEnrich.dataExtractor.mapJob', return_value=('Job', 'Comp', 'Desc')), \
             patch('aiEnrich.dataExtractor.logger') as mock_logger:
            mock_deps['ollama'].return_value = '{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": "REMOTE"}'
            assert dataExtractor() == 2
        started = [c.kwargs for c in mock_logger.info.call_args_list if c.args and c.args[0] == "job.started"]
        assert [entry['index'] for entry in started] == [1, 2]

    @patch('aiEnrich.dataExtractor._getJobBatches', return_value=[[1]])
    def test_footer_receives_batch_and_job_elapsed(self, mock_ids, mock_deps):
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = (1, 'Job', 'Desc', 'Comp')
        with patch('aiEnrich.dataExtractor.mapJob', return_value=('Job', 'Comp', 'Desc')):
            mock_deps['ollama'].return_value = '{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": "REMOTE"}'
            assert dataExtractor() == 1
        assert mock_deps['footer'].call_count == 1
        args = mock_deps['footer'].call_args.args
        assert args[:3] == (1, 0, 1)
        assert 0 <= args[5] <= args[4]

    @patch('aiEnrich.dataExtractor._getJobBatches', return_value=[[1]])
    def test_job_work_runs_inside_the_job_context(self, mock_ids, mock_deps):
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


@pytest.mark.parametrize("env_val, expected", ENV_GET_PARAMS)
def test_get_backend(env_val, expected):
    if env_val is None:
        os.environ.pop("AI_ENRICH_BACKEND", None)
    else:
        os.environ["AI_ENRICH_BACKEND"] = env_val
    from aiEnrich.dataExtractor import get_backend
    assert get_backend() == expected


@pytest.mark.parametrize("env_val, expected", OPENROUTER_URL_PARAMS)
def test_get_openrouter_base_url(env_val, expected):
    if env_val is None:
        os.environ.pop("AI_ENRICH_OPENROUTER_BASE_URL", None)
    else:
        os.environ["AI_ENRICH_OPENROUTER_BASE_URL"] = env_val
    from aiEnrich.dataExtractor import get_openrouter_base_url
    assert get_openrouter_base_url() == expected


@pytest.mark.parametrize("env_val, expected", OPENROUTER_MODEL_PARAMS)
def test_get_openrouter_model(env_val, expected):
    if env_val is None:
        os.environ.pop("AI_ENRICH_OPENROUTER_MODEL", None)
    else:
        os.environ["AI_ENRICH_OPENROUTER_MODEL"] = env_val
    from aiEnrich.dataExtractor import get_openrouter_model
    assert get_openrouter_model() == expected


@pytest.mark.parametrize("env_val, expected", OPENROUTER_FALLBACK_PARAMS)
def test_get_openrouter_fallback_model(env_val, expected):
    if env_val is None:
        os.environ.pop("AI_ENRICH_OPENROUTER_FALLBACK_MODEL", None)
    else:
        os.environ["AI_ENRICH_OPENROUTER_FALLBACK_MODEL"] = env_val
    from aiEnrich.dataExtractor import get_openrouter_fallback_model
    assert get_openrouter_fallback_model() == expected


class TestCheckBackendAvailable:
    def test_exits_when_no_server_was_ever_resolved(self, monkeypatch):
        from aiEnrich import dataExtractor
        monkeypatch.setattr(dataExtractor, "_resolved_ollama_url", None)
        monkeypatch.setattr(dataExtractor, "_ollama_server_known", False)
        monkeypatch.setattr(dataExtractor, "ollama_consecutive_failures", 0)
        monkeypatch.setattr(dataExtractor, "get_backend", lambda: "ollama")
        monkeypatch.setattr(dataExtractor, "get_max_ollama_failures", lambda: 3)
        monkeypatch.setattr(dataExtractor, "ping_backend", lambda: False)
        with patch.object(dataExtractor, "logger") as mock_logger:
            assert dataExtractor._check_backend_available() is False
            assert dataExtractor._check_backend_available() is False
            with pytest.raises(SystemExit):
                dataExtractor._check_backend_available()
        mock_logger.critical.assert_called_once_with("ai.exit_threshold_reached", consecutive_failures=3)

    def test_keeps_retrying_when_the_resolved_server_is_unreachable(self, monkeypatch):
        """A sleeping LAN host must not stop the pipeline: once the server was reached,
        failures keep the cycle returning -1 so the pipeline waits until it answers again."""
        from aiEnrich import dataExtractor
        monkeypatch.setattr(dataExtractor, "_resolved_ollama_url", None)
        monkeypatch.setattr(dataExtractor, "_ollama_server_known", True)
        monkeypatch.setattr(dataExtractor, "ollama_consecutive_failures", 0)
        monkeypatch.setattr(dataExtractor, "get_backend", lambda: "ollama")
        monkeypatch.setattr(dataExtractor, "get_max_ollama_failures", lambda: 3)
        monkeypatch.setattr(dataExtractor, "ping_backend", lambda: False)
        assert [dataExtractor._check_backend_available() for _ in range(5)] == [False] * 5
        assert dataExtractor.ollama_consecutive_failures == 5
        monkeypatch.setattr(dataExtractor, "ping_backend", lambda: True)
        assert dataExtractor._check_backend_available() is True
        assert dataExtractor.ollama_consecutive_failures == 0


class TestPingBackend:
    def test_routes_to_ollama(self, monkeypatch):
        os.environ["AI_ENRICH_BACKEND"] = "ollama"
        from aiEnrich import dataExtractor
        monkeypatch.setattr(dataExtractor, "_resolved_ollama_url", None)
        monkeypatch.setattr(dataExtractor, "_ollama_server_known", False)
        with patch.object(dataExtractor, "resolve_ollama_url", return_value="http://host:11434") as mock_resolve, \
             patch.object(dataExtractor, "ping_openrouter") as mock_ping_or:
            assert dataExtractor.ping_backend() is True
        mock_resolve.assert_called_once()
        mock_ping_or.assert_not_called()
        assert dataExtractor._ollama_server_known is True

    def test_rediscovers_when_cached_server_stops_answering(self, monkeypatch):
        """A sleeping LAN host may come back on another address: the cached URL must be
        dropped and resolved again instead of being pinged forever."""
        from aiEnrich import dataExtractor
        monkeypatch.setattr(dataExtractor, "_resolved_ollama_url", "http://192.168.1.50:11434")
        monkeypatch.setattr(dataExtractor, "_ollama_server_known", True)
        with patch.object(dataExtractor, "get_backend", return_value="ollama"), \
             patch.object(dataExtractor, "_ping_url", return_value=False), \
             patch.object(dataExtractor, "resolve_ollama_url", return_value="http://192.168.1.77:11434") as mock_resolve, \
             patch.object(dataExtractor, "logger"):
            assert dataExtractor.ping_backend() is True
        mock_resolve.assert_called_once()
        assert dataExtractor._resolved_ollama_url == "http://192.168.1.77:11434"
        assert dataExtractor._ollama_server_known is True

    def test_stays_unreachable_when_rediscovery_finds_nothing(self, monkeypatch):
        from aiEnrich import dataExtractor
        monkeypatch.setattr(dataExtractor, "_resolved_ollama_url", "http://192.168.1.50:11434")
        monkeypatch.setattr(dataExtractor, "_ollama_server_known", True)
        with patch.object(dataExtractor, "get_backend", return_value="ollama"), \
             patch.object(dataExtractor, "_ping_url", return_value=False), \
             patch.object(dataExtractor, "resolve_ollama_url", return_value=None), \
             patch.object(dataExtractor, "logger"):
            assert dataExtractor.ping_backend() is False
        assert dataExtractor._resolved_ollama_url is None
        assert dataExtractor._ollama_server_known is True

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
        repo.count_pending_enrichment.return_value = 0
        repo.get_job_to_enrich.return_value = (1, "Job", "Desc", "Comp")
        with patch("aiEnrich.dataExtractor.mapJob", return_value=("Job", "Comp", "Desc")), \
             patch("aiEnrich.dataExtractor.ping_backend", return_value=True), \
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
        repo.count_pending_enrichment.return_value = 0
        repo.get_job_to_enrich.return_value = (1, "Job", "Desc", "Comp")
        response = OllamaResponse(text='{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": "REMOTE"}',
                                 url="http://ollama", done=True, done_reason="stop")
        with patch("aiEnrich.dataExtractor.mapJob", return_value=("Job", "Comp", "Desc")), \
             patch("aiEnrich.dataExtractor.ping_backend", return_value=True), \
             patch("aiEnrich.dataExtractor.query_openrouter") as mock_or, \
             patch("aiEnrich.dataExtractor.query_ollama", return_value=response) as mock_ollama, \
             patch("aiEnrich.dataExtractor._save") as mock_save, \
             patch("aiEnrich.dataExtractor.validateResult"), \
             patch("aiEnrich.dataExtractor.footer"), \
             patch("aiEnrich.dataExtractor.stopWatch"):
            _process_job_safe(repo, 1, 1, 0, "enrich")
        mock_ollama.assert_called_once()
        assert mock_ollama.call_args.kwargs["return_metadata"] is True
        assert mock_ollama.call_args.kwargs["response_schema"]["required"] == ["required_technologies", "optional_technologies", "salary", "modality"]
        mock_or.assert_not_called()
        mock_save.assert_called_once()

    @pytest.mark.parametrize("llm_modality, expected_modality", [
        ("REMOTE", "REMOTE"),          # valid LLM modality overwrites scrape-time value
        ("hybrid", "HYBRID"),          # valid LLM modality is normalized and overwrites
        ("ON_SITE", "ON_SITE"),        # valid LLM modality overwrites scrape-time value
        (None, None),                  # null modality -> COALESCE keeps scrape-time value
        ("INVALID", None),             # invalid modality -> None -> COALESCE keeps scrape-time value
    ])
    def test_llm_modality_passthrough_to_update_enrichment(self, llm_modality, expected_modality):
        """LLM-inferred modality is passed to update_enrichment without being overwritten by extract_modality.
        Valid LLM modality overwrites the scrape-time deterministic value; None/invalid keeps it via COALESCE."""
        os.environ["AI_ENRICH_BACKEND"] = "ollama"
        from aiEnrich.dataExtractor import _process_job_safe
        repo = MagicMock()
        repo.count_pending_enrichment.return_value = 0
        repo.get_job_to_enrich.return_value = (1, "Job", "Desc", "Comp")
        payload = {"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": llm_modality}
        # Patch query_and_parse directly so schema validation doesn't reject non-enum modalities;
        # in production validateResult normalizes modality before _save passes it to update_enrichment.
        with patch("aiEnrich.dataExtractor.mapJob", return_value=("Job", "Comp", "Desc")), \
             patch("aiEnrich.dataExtractor.ping_backend", return_value=True), \
             patch("aiEnrich.dataExtractor.query_and_parse", return_value=(payload, MagicMock())), \
             patch("aiEnrich.dataExtractor.resolve_unspecified_company"), \
             patch("aiEnrich.dataExtractor.footer"), \
             patch("aiEnrich.dataExtractor.stopWatch"):
            _process_job_safe(repo, 1, 1, 0, "enrich")
        repo.update_enrichment.assert_called_once()
        assert repo.update_enrichment.call_args.args[4] == expected_modality
