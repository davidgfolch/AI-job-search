from unittest.mock import patch

from ..enrichRunner import dataExtractor, retry_failed_jobs

from .enrichRunner_fixtures import mock_deps, clean_env  # noqa: F401 - the fixtures register by being imported here
from .dataExtractor_mocks import ENRICHMENT_JSON, JOB_ROW, selector, selector_patches


class TestDataExtractor:
    @patch('aiEnrich.enrichRunner._getJobBatches', return_value=[[1]])
    def test_extractor_success(self, mock_ids, mock_deps):
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = JOB_ROW
        mock_deps['ollama'].return_value = ENRICHMENT_JSON
        assert dataExtractor() == 1
        mock_deps['save'].assert_called()
        mock_deps['ollama'].assert_called_once()

    @patch('aiEnrich.enrichRunner._getJobBatches', return_value=[[1]])
    def test_skips_when_ollama_down(self, mock_ids, mock_deps):
        mock_deps['ping'].return_value = False
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        assert dataExtractor() == -1
        mock_deps['ollama'].assert_not_called()
        mock_deps['save'].assert_not_called()

    @patch('aiEnrich.enrichRunner._getJobBatches', return_value=[[1]])
    def test_marks_job_error_when_ollama_is_up_but_returns_none(self, mock_ids, mock_deps):
        """A backend that answers the probe but never replies must not keep the job pending."""
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = JOB_ROW
        mock_deps['ollama'].return_value = None
        assert dataExtractor() == 1
        mock_deps['save'].assert_not_called()
        assert mock_deps['ollama'].call_count == 1
        mock_deps['repo'].update_enrichment_error.assert_called_once()
        assert mock_deps['repo'].update_enrichment_error.call_args.args[1].startswith("no response from ollama")

    @patch('aiEnrich.enrichRunner._getJobBatches', return_value=[[1, 2]])
    def test_job_started_index_is_one_based(self, mock_ids, mock_deps):
        mock_deps['repo'].count_pending_enrichment.return_value = 2
        mock_deps['repo'].get_job_to_enrich.return_value = JOB_ROW
        mock_deps['ollama'].return_value = ENRICHMENT_JSON
        with patch('aiEnrich.dataExtractor.logger') as mock_logger:
            assert dataExtractor() == 2
        started = [c.kwargs for c in mock_logger.info.call_args_list if c.args and c.args[0] == "job.started"]
        assert [entry['index'] for entry in started] == [1, 2]

    @patch('aiEnrich.enrichRunner._getJobBatches', return_value=[[1]])
    def test_footer_receives_batch_and_job_elapsed(self, mock_ids, mock_deps):
        mock_deps['repo'].count_pending_enrichment.return_value = 1
        mock_deps['repo'].get_job_to_enrich.return_value = JOB_ROW
        mock_deps['ollama'].return_value = ENRICHMENT_JSON
        assert dataExtractor() == 1
        assert mock_deps['footer'].call_count == 1
        args = mock_deps['footer'].call_args.args
        assert args[:3] == (1, 0, 1)
        assert 0 <= args[5] <= args[4]


class TestFcRecheck:
    @patch('aiEnrich.enrichRunner._getJobBatches', return_value=[[1]])
    def test_skips_job_if_not_matching_current_fc(self, mock_ids, mock_deps):
        repo = mock_deps['repo']
        repo.count_pending_enrichment.return_value = 1
        repo.config_for_job.return_value = "MyFC"
        with selector_patches(selector(["MyFC"], [])):
            assert dataExtractor() == 1
        repo.get_job_to_enrich.assert_not_called()
        mock_deps['ollama'].assert_not_called()

    @patch('aiEnrich.enrichRunner._getJobBatches', return_value=[[1]])
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

    def test_keeps_the_job_when_no_configuration_is_loaded(self, mock_deps):
        """A configuration-less database leaves the batch as it was instead of emptying it."""
        repo = mock_deps['repo']
        repo.count_pending_enrichment.return_value = 1
        repo.config_for_job.return_value = "MyFC"
        repo.get_job_to_enrich.return_value = JOB_ROW
        mock_deps['ollama'].return_value = ENRICHMENT_JSON
        with patch('aiEnrich.enrichRunner._getJobBatches', return_value=[[1]]), \
             selector_patches(selector([], [])) as _:
            assert dataExtractor() == 1
        repo.get_job_to_enrich.assert_called_once_with(1)

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
