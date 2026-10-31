import pytest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from ..dataExtractor import dataExtractor, retry_failed_jobs, _save, _process_job_safe, _notify_watcher_backend

from .dataExtractor_fixtures import (
    mock_deps, clean_env,  # noqa: F401 - the fixtures register by being imported here
)
from .dataExtractor_mocks import (
    ENRICHMENT_JSON, JOB_ROW, enrich_repo, ollama_response, process_job_patches, selector, selector_patches,
)


class TestDataExtractor:
    @patch('aiEnrich.dataExtractor._getJobBatches', return_value=[[1]])
    def test_extractor_success(self, mock_ids, mock_deps):
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = JOB_ROW
        mock_deps['ollama'].return_value = ENRICHMENT_JSON
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
        mock_deps['repo'].get_job_to_enrich.return_value = JOB_ROW
        mock_deps['ollama'].side_effect = [None, ENRICHMENT_JSON]
        assert dataExtractor() == 1
        mock_deps['save'].assert_called_once()
        assert mock_deps['ollama'].call_count == 2

    def test_save(self, mock_deps):
        repo = MagicMock()
        with patch('aiEnrich.dataExtractor.validateResult'), patch('aiEnrich.dataExtractor._notify_watcher_backend') as notify:
            _save(repo, 1, {'salary': '100k', 'required_technologies': 'T', 'optional_technologies': 'O', 'modality': ['REMOTE']})
        repo.update_enrichment.assert_called_once_with(1, '100k', 'T', 'O', ['REMOTE'])
        notify.assert_called_once_with([1])

    @patch('aiEnrich.dataExtractor._getJobBatches', return_value=[[1, 2]])
    def test_job_started_index_is_one_based(self, mock_ids, mock_deps):
        mock_deps['repo'].count_pending_enrichment.return_value = 2
        mock_deps['repo'].get_job_to_enrich.return_value = JOB_ROW
        mock_deps['ollama'].return_value = ENRICHMENT_JSON
        with patch('aiEnrich.dataExtractor.logger') as mock_logger:
            assert dataExtractor() == 2
        started = [c.kwargs for c in mock_logger.info.call_args_list if c.args and c.args[0] == "job.started"]
        assert [entry['index'] for entry in started] == [1, 2]

    @patch('aiEnrich.dataExtractor._getJobBatches', return_value=[[1]])
    def test_footer_receives_batch_and_job_elapsed(self, mock_ids, mock_deps):
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = JOB_ROW
        mock_deps['ollama'].return_value = ENRICHMENT_JSON
        assert dataExtractor() == 1
        assert mock_deps['footer'].call_count == 1
        args = mock_deps['footer'].call_args.args
        assert args[:3] == (1, 0, 1)
        assert 0 <= args[5] <= args[4]

    @patch('aiEnrich.dataExtractor._getJobBatches', return_value=[[1]])
    def test_job_work_runs_inside_the_job_context(self, mock_ids, mock_deps):
        order = []
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = JOB_ROW
        mock_deps['ollama'].return_value = ENRICHMENT_JSON

        @contextmanager
        def spy(job_id):
            order.append(('enter', job_id))
            yield
            order.append(('exit', job_id))

        mock_deps['save'].side_effect = lambda *a, **k: order.append(('save', None))
        with patch('aiEnrich.dataExtractor.job_log_context', spy):
            assert dataExtractor() == 1
        assert order[0] == ('enter', 1)
        assert ('save', None) in order
        assert order.index(('save', None)) < order.index(('exit', 1))


class TestProcessJobSafeBackend:
    def test_uses_openrouter_when_backend_openrouter(self):
        repo = enrich_repo()
        with process_job_patches(backend="openrouter") as deps:
            deps.openrouter.return_value = ENRICHMENT_JSON
            _process_job_safe(repo, 1, 1, 0, "enrich")
        deps.openrouter.assert_called_once()
        deps.ollama.assert_not_called()
        deps.save.assert_called_once()

    def test_uses_ollama_when_backend_ollama(self):
        repo = enrich_repo()
        with process_job_patches() as deps:
            deps.ollama.return_value = ollama_response()
            _process_job_safe(repo, 1, 1, 0, "enrich")
        deps.ollama.assert_called_once()
        assert deps.ollama.call_args.kwargs["return_metadata"] is True
        assert deps.ollama.call_args.kwargs["response_schema"]["required"] == ["required_technologies", "optional_technologies", "salary", "modality"]
        deps.openrouter.assert_not_called()
        deps.save.assert_called_once()

    @pytest.mark.parametrize("llm_modality, expected_modality", [
        (["REMOTE"], ["REMOTE"]),                      # valid LLM modality overwrites scrape-time value
        (["hybrid"], ["HYBRID"]),                      # valid LLM modality is normalized and overwrites
        (["ON_SITE"], ["ON_SITE"]),                    # valid LLM modality overwrites scrape-time value
        (["HYBRID", "REMOTE"], ["REMOTE", "HYBRID"]),  # several arrangements kept in canonical order
        (None, None),                                  # null modality -> COALESCE keeps scrape-time value
        (["INVALID"], None),                           # invalid modality -> None -> COALESCE keeps scrape-time value
    ])
    def test_llm_modality_passthrough_to_update_enrichment(self, llm_modality, expected_modality):
        """LLM-inferred modality is passed to update_enrichment without being overwritten by extract_modalities.
        Valid LLM modality overwrites the scrape-time deterministic value; None/invalid keeps it via COALESCE."""
        repo = enrich_repo()
        payload = {"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": llm_modality}
        with process_job_patches(fake_save=False, fake_parse=True) as deps:
            deps.query_and_parse.return_value = (payload, MagicMock())
            _process_job_safe(repo, 1, 1, 0, "enrich")
        repo.update_enrichment.assert_called_once()
        assert repo.update_enrichment.call_args.args[4] == expected_modality


class TestNotifyWatcherBackend:
    @patch("aiEnrich.dataExtractor.notify_backend_watcher")
    @patch("aiEnrich.dataExtractor.get_backend_url", return_value="http://backend:8000/")
    def test_delegates_to_shared_client(self, mock_url, mock_notify):
        _notify_watcher_backend([1, 2])
        mock_notify.assert_called_once_with([1, 2], base_url="http://backend:8000/")

    @patch("aiEnrich.dataExtractor.notify_backend_watcher")
    def test_empty_ids_skip_request(self, mock_notify):
        _notify_watcher_backend([])
        mock_notify.assert_not_called()


class TestFcRecheck:
    @patch('aiEnrich.dataExtractor._getJobBatches', return_value=[[1]])
    def test_skips_job_if_not_matching_current_fc(self, mock_ids, mock_deps):
        repo = mock_deps['repo']
        repo.count_pending_enrichment.return_value = 1
        repo.config_for_job.return_value = "MyFC"
        with selector_patches(selector(["MyFC"], [])):
            assert dataExtractor() == 1
        repo.get_job_to_enrich.assert_not_called()
        mock_deps['ollama'].assert_not_called()

    @patch('aiEnrich.dataExtractor._getJobBatches', return_value=[[1]])
    def test_updates_config_when_matches_current_fc(self, mock_ids, mock_deps):
        repo = mock_deps['repo']
        repo.count_pending_enrichment.return_value = 1
        repo.config_for_job.return_value = "OldFC"
        repo.get_job_to_enrich.return_value = JOB_ROW
        mock_deps['ollama'].return_value = ENRICHMENT_JSON
        with selector_patches(selector(["NewFC"], [1])):
            assert dataExtractor() == 1
        assert repo._job_configs[1] == "NewFC"
        mock_deps['save'].assert_called()

    def test_retry_skips_if_not_matching_current_fc(self, mock_deps):
        repo = mock_deps['repo']
        repo.get_enrichment_error_id_retry.return_value = 5
        repo.config_for_job.return_value = "MyFC"
        with selector_patches(selector(["MyFC"], [])):
            assert retry_failed_jobs() == 1
        repo.get_job_to_retry.assert_not_called()

    def test_retry_updates_config_when_matches_current_fc(self, mock_deps):
        repo = mock_deps['repo']
        repo.get_enrichment_error_id_retry.return_value = 5
        repo.config_for_job.return_value = "OldFC"
        repo.get_job_to_retry.return_value = (5, 'Job', 'Desc', 'Comp')
        mock_deps['ollama'].return_value = ENRICHMENT_JSON
        with selector_patches(selector(["NewFC"], [5])):
            assert retry_failed_jobs() == 1
        assert repo._job_configs[5] == "NewFC"


class TestProcessJobSafeTooLongContext:
    def test_oversized_context_is_marked_without_calling_the_model(self, monkeypatch):
        monkeypatch.setenv("AI_ENRICH_INPUT_MAX_LEN", "10")
        repo = enrich_repo()
        with process_job_patches() as deps, patch("aiEnrich.dataExtractor.footer") as footer:
            _process_job_safe(repo, 1, 1, 0, "enrich")
        repo.skip_enrichment.assert_called_once_with(1)
        deps.ollama.assert_not_called()
        deps.openrouter.assert_not_called()
        deps.save.assert_not_called()
        footer.assert_called_once()

    def test_short_context_still_calls_the_model(self, monkeypatch):
        monkeypatch.setenv("AI_ENRICH_INPUT_MAX_LEN", "100000")
        repo = enrich_repo()
        with process_job_patches() as deps:
            deps.ollama.return_value = ollama_response()
            _process_job_safe(repo, 1, 1, 0, "enrich")
        repo.skip_enrichment.assert_not_called()
        deps.ollama.assert_called_once()
