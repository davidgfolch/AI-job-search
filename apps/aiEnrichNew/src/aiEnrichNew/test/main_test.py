import unittest
from unittest.mock import MagicMock, patch
from ..main import run


class TestMain(unittest.TestCase):
    def assertIdle(self, mock_idle_wait, event, reason):
        self.assertTrue(
            any(call.args[1:] == ("10s", event) and call.kwargs == {"reason": reason} for call in mock_idle_wait.call_args_list),
            mock_idle_wait.call_args_list,
        )

    @patch("aiEnrichNew.main.get_job_enabled", return_value=True)
    @patch("aiEnrichNew.main.dataExtractor")
    @patch("aiEnrichNew.main.retry_failed_jobs")
    @patch("aiEnrichNew.main.logIdleWait")
    @patch("aiEnrichNew.main.cyan", side_effect=lambda x: x)
    def test_run_idle_after_no_jobs(self, mock_cyan, mock_idle_wait, mock_retry_failed_jobs, mock_dataExtractor, mock_get_job_enabled):
        mock_retry_failed_jobs.return_value = 0
        mock_dataExtractor.side_effect = [0, Exception("BreakLoop")]
        try:
            run()
        except Exception as e:
            if str(e) != "BreakLoop":
                raise e
        mock_retry_failed_jobs.assert_called_once()
        self.assertIdle(mock_idle_wait, "jobs.skipped", "no_pending_jobs")

    @patch("aiEnrichNew.main.get_job_enabled", return_value=True)
    @patch("aiEnrichNew.main.dataExtractor")
    @patch("aiEnrichNew.main.retry_failed_jobs")
    @patch("aiEnrichNew.main.logIdleWait")
    @patch("aiEnrichNew.main.cyan", side_effect=lambda x: x)
    def test_run_idle_after_retry_cycle(self, mock_cyan, mock_idle_wait, mock_retry_failed_jobs, mock_dataExtractor, mock_get_job_enabled):
        mock_retry_failed_jobs.return_value = 0
        mock_dataExtractor.side_effect = [0, Exception("BreakLoop")]
        try:
            run()
        except Exception as e:
            if str(e) != "BreakLoop":
                raise e
        mock_retry_failed_jobs.assert_called_once()
        self.assertIdle(mock_idle_wait, "jobs.skipped", "no_pending_jobs")

    @patch("aiEnrichNew.main.get_job_enabled", return_value=True)
    @patch("aiEnrichNew.main.dataExtractor")
    @patch("aiEnrichNew.main.retry_failed_jobs")
    @patch("aiEnrichNew.main.logIdleWait")
    @patch("aiEnrichNew.main.cyan", side_effect=lambda x: x)
    def test_run_data_extractor_nonzero(self, mock_cyan, mock_idle_wait, mock_retry_failed_jobs, mock_dataExtractor, mock_get_job_enabled):
        mock_dataExtractor.side_effect = [1, Exception("BreakLoop")]
        try:
            run()
        except Exception as e:
            if str(e) != "BreakLoop":
                raise e
        mock_retry_failed_jobs.assert_not_called()
        mock_idle_wait.assert_not_called()

    @patch("aiEnrichNew.main.get_job_enabled", return_value=True)
    @patch("aiEnrichNew.main.dataExtractor")
    @patch("aiEnrichNew.main.retry_failed_jobs")
    @patch("aiEnrichNew.main.logIdleWait")
    @patch("aiEnrichNew.main.cyan", side_effect=lambda x: x)
    def test_run_retry_failed_jobs_nonzero(self, mock_cyan, mock_idle_wait, mock_retry_failed_jobs, mock_dataExtractor, mock_get_job_enabled):
        mock_dataExtractor.return_value = 0
        mock_retry_failed_jobs.return_value = 1
        mock_dataExtractor.side_effect = [0, Exception("BreakLoop")]
        try:
            run()
        except Exception as e:
            if str(e) != "BreakLoop":
                raise e
        mock_retry_failed_jobs.assert_called()


if __name__ == "__main__":
    unittest.main()