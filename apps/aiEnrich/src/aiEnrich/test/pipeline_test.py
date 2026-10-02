import pytest
from unittest.mock import patch, MagicMock
from commonlib.terminalColor import cyan


def assert_any_idle(mock_idle_wait, text, event, reason):
    """Assert the idle wait logged `event` with `reason` for the given console text."""
    assert any(
        call.args[1:] == ("10s", event) and call.kwargs == {"reason": reason} and call.args[0] == text
        for call in mock_idle_wait.call_args_list
    ), mock_idle_wait.call_args_list


class TestPipeline:

    @patch('aiEnrich.pipeline.retry_failed_jobs')
    @patch('aiEnrich.pipeline.dataExtractor', side_effect=[1, 0])
    @patch('aiEnrich.pipeline.logIdleWait')
    def test_run_pipeline_enriches_then_done(self, mock_idle_wait,
                                             mock_data_extractor,
                                             mock_retry_failed_jobs):
        from ..pipeline import run_pipeline

        mock_retry_failed_jobs.side_effect = [0]

        try:
            run_pipeline()
        except StopIteration:
            pass

        assert mock_data_extractor.call_count == 3
        mock_retry_failed_jobs.assert_called_once()
        assert_any_idle(mock_idle_wait, cyan('All jobs enriched.'), 'jobs.skipped', 'no_pending_jobs')

    @patch('aiEnrich.pipeline.retry_failed_jobs')
    @patch('aiEnrich.pipeline.dataExtractor', side_effect=[-1, 0])
    @patch('aiEnrich.pipeline.logIdleWait')
    def test_run_pipeline_retries_when_backend_unavailable(self, mock_idle_wait,
                                                           mock_data_extractor,
                                                           mock_retry_failed_jobs):
        from ..pipeline import run_pipeline

        mock_retry_failed_jobs.side_effect = [0]

        try:
            run_pipeline()
        except StopIteration:
            pass

        assert mock_data_extractor.call_count == 3
        mock_retry_failed_jobs.assert_called_once()
        assert_any_idle(mock_idle_wait, cyan('Backend unavailable, retrying... '), 'ai.retry_wait', 'backend_unavailable')
        assert_any_idle(mock_idle_wait, cyan('All jobs enriched.'), 'jobs.skipped', 'no_pending_jobs')

    @patch('aiEnrich.pipeline.retry_failed_jobs')
    @patch('aiEnrich.pipeline.dataExtractor', side_effect=[0, 0])
    @patch('aiEnrich.pipeline.logIdleWait')
    def test_run_pipeline_retries_when_retry_backend_unavailable(self, mock_idle_wait,
                                                                 mock_data_extractor,
                                                                 mock_retry_failed_jobs):
        from ..pipeline import run_pipeline

        mock_retry_failed_jobs.side_effect = [-1, 0]

        try:
            run_pipeline()
        except StopIteration:
            pass

        assert mock_data_extractor.call_count == 3
        assert mock_retry_failed_jobs.call_count == 2
        assert_any_idle(mock_idle_wait, cyan('Backend unavailable, retrying... '), 'ai.retry_wait', 'backend_unavailable')
        assert_any_idle(mock_idle_wait, cyan('All jobs enriched.'), 'jobs.skipped', 'no_pending_jobs')