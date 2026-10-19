import os
import pytest
from contextlib import contextmanager
from unittest.mock import patch, MagicMock

from commonlib.ollama_client import OllamaResponse
from ..dataExtractor import dataExtractor, _save, _process_job_safe

from .dataExtractor_fixtures import (
    mock_deps, clean_env,
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


class TestProcessJobSafeBackend:
    def test_uses_openrouter_when_backend_openrouter(self):
        os.environ["AI_ENRICH_BACKEND"] = "openrouter"
        repo = MagicMock()
        repo.count_pending_enrichment.return_value = 0
        repo.get_job_to_enrich.return_value = (1, "Job", "Desc", "Comp")
        with patch("aiEnrich.dataExtractor.mapJob", return_value=("Job", "Comp", "Desc")), \
             patch("aiEnrich.dataExtractor.ping_backend", return_value=True), \
             patch("aiEnrich.ollama_backend.query_openrouter", return_value='{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": "REMOTE"}') as mock_or, \
             patch("aiEnrich.ollama_backend.query_ollama") as mock_ollama, \
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
        repo = MagicMock()
        repo.count_pending_enrichment.return_value = 0
        repo.get_job_to_enrich.return_value = (1, "Job", "Desc", "Comp")
        response = OllamaResponse(text='{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": "REMOTE"}',
                                 url="http://ollama", done=True, done_reason="stop")
        with patch("aiEnrich.dataExtractor.mapJob", return_value=("Job", "Comp", "Desc")), \
             patch("aiEnrich.dataExtractor.ping_backend", return_value=True), \
             patch("aiEnrich.ollama_backend.query_openrouter") as mock_or, \
             patch("aiEnrich.ollama_backend.query_ollama", return_value=response) as mock_ollama, \
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
        repo = MagicMock()
        repo.count_pending_enrichment.return_value = 0
        repo.get_job_to_enrich.return_value = (1, "Job", "Desc", "Comp")
        payload = {"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": llm_modality}
        with patch("aiEnrich.dataExtractor.mapJob", return_value=("Job", "Comp", "Desc")), \
             patch("aiEnrich.dataExtractor.ping_backend", return_value=True), \
             patch("aiEnrich.dataExtractor.query_and_parse", return_value=(payload, MagicMock())), \
             patch("aiEnrich.dataExtractor.resolve_unspecified_company"), \
             patch("aiEnrich.dataExtractor.footer"), \
             patch("aiEnrich.dataExtractor.stopWatch"):
            _process_job_safe(repo, 1, 1, 0, "enrich")
        repo.update_enrichment.assert_called_once()
        assert repo.update_enrichment.call_args.args[4] == expected_modality
