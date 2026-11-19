import pytest
from unittest.mock import MagicMock, patch

from commonlib.ai_helpers import RETRY_ERROR_PREFIX

from ..dataExtractor import _save, _process_job_safe, _notify_watcher_backend
from ..enrichRunner import retry_failed_jobs

from .dataExtractor_mocks import (
    ENRICHMENT_JSON, enrich_repo, ollama_response, process_job_patches,
)


class TestSave:
    def test_save(self, mock_deps=None):
        repo = MagicMock()
        with patch('aiEnrich.dataExtractor.validateResult'), patch('aiEnrich.dataExtractor._notify_watcher_backend') as notify:
            _save(repo, 1, {'salary': '100k', 'required_technologies': 'T', 'optional_technologies': 'O', 'modality': ['REMOTE'], 'hybrid_info': '2 days office'})
        repo.update_enrichment.assert_called_once_with(1, '100k', 'T', 'O', ['REMOTE'], '2 days office')
        notify.assert_called_once_with([1])


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
        assert deps.ollama.call_args.kwargs["response_schema"]["required"] == ["required_technologies", "optional_technologies", "salary", "modality", "hybrid_info"]
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
        payload = {"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": llm_modality, "hybrid_info": None}
        with process_job_patches(fake_save=False, fake_parse=True) as deps:
            deps.query_and_parse.return_value = (payload, MagicMock())
            _process_job_safe(repo, 1, 1, 0, "enrich")
        repo.update_enrichment.assert_called_once()
        assert repo.update_enrichment.call_args.args[4] == expected_modality

    def test_ungrounded_technologies_never_reach_update_enrichment(self):
        repo = enrich_repo()
        payload = {"required_technologies": ["Java"], "optional_technologies": ["Docker", "Kubernetes"], "salary": None, "modality": ["REMOTE"], "hybrid_info": None}
        with process_job_patches(fake_save=False, fake_parse=True) as deps, \
             patch("aiEnrich.dataExtractor.mapJob", return_value=("Job", "Comp", "Oferta con Java y Spring Boot")):
            deps.query_and_parse.return_value = (payload, MagicMock())
            _process_job_safe(repo, 1, 1, 0, "enrich")
        repo.update_enrichment.assert_called_once()
        assert repo.update_enrichment.call_args.args[1:] == (None, "Java", None, ["REMOTE"], None)

    def test_hallucinated_hybrid_info_never_reaches_update_enrichment(self):
        repo = enrich_repo()
        payload = {"required_technologies": ["Java"], "optional_technologies": [], "salary": None, "modality": ["REMOTE"],
                   "hybrid_info": "Hybrid work, with 2 days per week in the office and 5 days per week remote, with a flexible schedule."}
        with process_job_patches(fake_save=False, fake_parse=True) as deps, \
             patch("aiEnrich.dataExtractor.mapJob", return_value=("Job", "Comp", "Remote, Full-time. Backend in Java.")):
            deps.query_and_parse.return_value = (payload, MagicMock())
            _process_job_safe(repo, 1, 1, 0, "enrich")
        repo.update_enrichment.assert_called_once()
        assert repo.update_enrichment.call_args.args[4:] == (["REMOTE"], None)


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

    @pytest.mark.parametrize("process_name, prefix", [("enrich", ""), ("retry", "RETRY ERROR: ")])
    def test_backend_up_without_a_reply_marks_ai_enrich_error(self, process_name, prefix):
        repo = enrich_repo()
        with process_job_patches() as deps:
            deps.ollama.return_value = None
            _process_job_safe(repo, 1, 1, 0, process_name)
        repo.update_enrichment_error.assert_called_once()
        error_msg, is_enrichment = repo.update_enrichment_error.call_args.args[1:]
        assert error_msg.startswith(f"{prefix}no response from ollama (timeout ")
        assert is_enrichment is True
        assert deps.ollama.call_count == 1
        deps.save.assert_not_called()

    def test_backend_going_down_mid_job_waits_instead_of_marking_an_error(self):
        repo = enrich_repo()
        with process_job_patches() as deps, \
             patch("aiEnrich.dataExtractor.ping_backend", side_effect=[True, False, True]), \
             patch("aiEnrich.dataExtractor.logIdleWait") as idle:
            deps.ollama.side_effect = [None, ollama_response()]
            _process_job_safe(repo, 1, 1, 0, "enrich")
        idle.assert_called_once()
        assert idle.call_args.kwargs == {"reason": "backend_unavailable"}
        repo.update_enrichment_error.assert_not_called()
        deps.save.assert_called_once()

    def test_short_context_still_calls_the_model(self, monkeypatch):
        monkeypatch.setenv("AI_ENRICH_INPUT_MAX_LEN", "100000")
        repo = enrich_repo()
        with process_job_patches() as deps:
            deps.ollama.return_value = ollama_response()
            _process_job_safe(repo, 1, 1, 0, "enrich")
        repo.skip_enrichment.assert_not_called()
        deps.ollama.assert_called_once()


class TestErrorRetryPass:
    """A job Ollama cannot answer leaves the queue after one retry pass instead of looping forever.

    The repository double mirrors the guard the real query applies (an error already prefixed with
    RETRY_ERROR_PREFIX is not selected again); aiEnrichRepository_test asserts that guard in the SQL.
    """

    @staticmethod
    def _repo(job_id: int):
        state = {"error": ""}
        repo = enrich_repo(job_id)
        repo.config_for_job.return_value = None
        repo.count_pending_enrichment.return_value = 0
        repo.update_enrichment_error.side_effect = lambda _id, msg, _flag: state.update(error=msg) or 1
        repo.get_enrichment_error_id_retry.side_effect = lambda: job_id if state["error"] and not state["error"].startswith(RETRY_ERROR_PREFIX) else None
        return repo, state

    def test_marked_job_is_retried_once_and_then_left_alone(self):
        job_id = 42
        repo, state = self._repo(job_id)
        with process_job_patches() as deps, \
             patch("aiEnrich.enrichRunner.MysqlUtil"), \
             patch("aiEnrich.enrichRunner.AiEnrichRepository", return_value=repo), \
             patch("aiEnrich.enrichRunner._check_backend_available", return_value=True):
            deps.ollama.return_value = None
            # The enrich pass writes an unprefixed error, which is exactly what the retry pass selects.
            _process_job_safe(repo, job_id, 1, 0, "enrich")
            assert state["error"].startswith("no response from ollama")
            assert not state["error"].startswith(RETRY_ERROR_PREFIX)

            assert retry_failed_jobs() == 1
            assert state["error"].startswith(f"{RETRY_ERROR_PREFIX}no response from ollama")
            assert repo.get_job_to_retry.call_count == 1

            # Second pass: the prefixed error is no longer selected, so the job never reaches Ollama again.
            deps.ollama.reset_mock()
            assert retry_failed_jobs() == 0
            assert repo.get_job_to_retry.call_count == 1
            deps.ollama.assert_not_called()
