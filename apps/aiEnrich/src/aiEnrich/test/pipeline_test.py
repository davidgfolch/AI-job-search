import pytest
from unittest.mock import patch, MagicMock


class TestPipeline:

    @patch('aiEnrich.pipeline.retry_failed_jobs')
    @patch('aiEnrich.pipeline.dataExtractor')
    @patch('aiEnrich.pipeline.consoleTimer')
    @patch('aiEnrich.pipeline.printHR')
    def test_run_pipeline(self, mock_print_hr, mock_console_timer,
                          mock_data_extractor,
                          mock_retry_failed_jobs):
        from ..pipeline import run_pipeline

        mock_data_extractor.side_effect = [1, 0, 0]
        mock_retry_failed_jobs.side_effect = [0, 0]

        try:
            run_pipeline()
        except StopIteration:
            pass

        assert mock_data_extractor.call_count >= 1
