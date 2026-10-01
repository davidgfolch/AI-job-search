import pytest
from unittest.mock import patch, MagicMock
from commonlib.terminalColor import cyan


class TestPipeline:

    @patch('aiEnrich.pipeline.retry_failed_jobs')
    @patch('aiEnrich.pipeline.dataExtractor', side_effect=[1, 0])
    @patch('aiEnrich.pipeline.consoleTimer')
    def test_run_pipeline_enriches_then_done(self, mock_console_timer,
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
        mock_console_timer.assert_any_call(cyan('All jobs enriched. '), '10s', end='\n')

    @patch('aiEnrich.pipeline.retry_failed_jobs')
    @patch('aiEnrich.pipeline.dataExtractor', side_effect=[-1, 0])
    @patch('aiEnrich.pipeline.consoleTimer')
    def test_run_pipeline_retries_when_backend_unavailable(self, mock_console_timer,
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
        mock_console_timer.assert_any_call(cyan('Backend unavailable, retrying... '), '10s', end='\n')
        mock_console_timer.assert_any_call(cyan('All jobs enriched. '), '10s', end='\n')

    @patch('aiEnrich.pipeline.retry_failed_jobs')
    @patch('aiEnrich.pipeline.dataExtractor', side_effect=[0, 0])
    @patch('aiEnrich.pipeline.consoleTimer')
    def test_run_pipeline_retries_when_retry_backend_unavailable(self, mock_console_timer,
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
        mock_console_timer.assert_any_call(cyan('Backend unavailable, retrying... '), '10s', end='\n')
        mock_console_timer.assert_any_call(cyan('All jobs enriched. '), '10s', end='\n')