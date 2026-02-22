import unittest
from unittest.mock import MagicMock, patch
from ..main import run


class TestMain(unittest.TestCase):
    @patch("aiEnrichNew.main.dataExtractor")
    @patch("aiEnrichNew.main.skillEnricher")
    @patch("aiEnrichNew.main.retry_failed_jobs")
    @patch("aiEnrichNew.main.consoleTimer")
    @patch("aiEnrichNew.main.printHR")
    @patch("aiEnrichNew.main.cyan", side_effect=lambda x: x)
    @patch("time.sleep")
    def test_run_cv_match_enabled(
        self,
        mock_sleep,
        mock_cyan,
        mock_printHR,
        mock_consoleTimer,
        mock_retry_failed_jobs,
        mock_skillEnricher,
        mock_dataExtractor,
    ):
        mock_skillEnricher.return_value = 0
        mock_retry_failed_jobs.return_value = 0
        mock_dataExtractor.side_effect = [0, Exception("BreakLoop")]
        try:
            run()
        except Exception as e:
            if str(e) != "BreakLoop":
                raise e
        mock_skillEnricher.assert_called_once()
        mock_retry_failed_jobs.assert_called_once()
        mock_consoleTimer.assert_any_call("All jobs enriched. ", "10s", end="\r")

    @patch("aiEnrichNew.main.dataExtractor")
    @patch("aiEnrichNew.main.skillEnricher")
    @patch("aiEnrichNew.main.retry_failed_jobs")
    @patch("aiEnrichNew.main.consoleTimer")
    @patch("aiEnrichNew.main.printHR")
    @patch("aiEnrichNew.main.cyan", side_effect=lambda x: x)
    def test_run_cv_match_disabled(
        self,
        mock_cyan,
        mock_printHR,
        mock_consoleTimer,
        mock_retry_failed_jobs,
        mock_skillEnricher,
        mock_dataExtractor,
    ):
        mock_skillEnricher.return_value = 0
        mock_retry_failed_jobs.return_value = 0
        mock_dataExtractor.side_effect = [0, Exception("BreakLoop")]
        try:
            run()
        except Exception as e:
            if str(e) != "BreakLoop":
                raise e
        mock_skillEnricher.assert_called_once()
        mock_retry_failed_jobs.assert_called_once()
        mock_consoleTimer.assert_any_call("All jobs enriched. ", "10s", end="\r")

    @patch("aiEnrichNew.main.dataExtractor")
    @patch("aiEnrichNew.main.skillEnricher")
    @patch("aiEnrichNew.main.retry_failed_jobs")
    @patch("aiEnrichNew.main.consoleTimer")
    @patch("aiEnrichNew.main.printHR")
    @patch("aiEnrichNew.main.cyan", side_effect=lambda x: x)
    def test_run_data_extractor_nonzero(
        self,
        mock_cyan,
        mock_printHR,
        mock_consoleTimer,
        mock_retry_failed_jobs,
        mock_skillEnricher,
        mock_dataExtractor,
    ):
        mock_dataExtractor.side_effect = [1, Exception("BreakLoop")]
        try:
            run()
        except Exception as e:
            if str(e) != "BreakLoop":
                raise e
        mock_skillEnricher.assert_not_called()
        mock_retry_failed_jobs.assert_not_called()
        mock_consoleTimer.assert_not_called()

    @patch("aiEnrichNew.main.dataExtractor")
    @patch("aiEnrichNew.main.skillEnricher")
    @patch("aiEnrichNew.main.retry_failed_jobs")
    @patch("aiEnrichNew.main.consoleTimer")
    @patch("aiEnrichNew.main.printHR")
    @patch("aiEnrichNew.main.cyan", side_effect=lambda x: x)
    @patch("time.sleep")
    def test_run_skill_enricher_nonzero(
        self,
        mock_sleep,
        mock_cyan,
        mock_printHR,
        mock_consoleTimer,
        mock_retry_failed_jobs,
        mock_skillEnricher,
        mock_dataExtractor,
    ):
        mock_dataExtractor.return_value = 0
        mock_skillEnricher.return_value = 1
        mock_retry_failed_jobs.return_value = 0
        mock_dataExtractor.side_effect = [0, Exception("BreakLoop")]
        try:
            run()
        except Exception as e:
            if str(e) != "BreakLoop":
                raise e
        mock_skillEnricher.assert_called()

    @patch("aiEnrichNew.main.dataExtractor")
    @patch("aiEnrichNew.main.skillEnricher")
    @patch("aiEnrichNew.main.retry_failed_jobs")
    @patch("aiEnrichNew.main.consoleTimer")
    @patch("aiEnrichNew.main.printHR")
    @patch("aiEnrichNew.main.cyan", side_effect=lambda x: x)
    @patch("time.sleep")
    def test_run_retry_failed_jobs_nonzero(
        self,
        mock_sleep,
        mock_cyan,
        mock_printHR,
        mock_consoleTimer,
        mock_retry_failed_jobs,
        mock_skillEnricher,
        mock_dataExtractor,
    ):
        mock_dataExtractor.return_value = 0
        mock_skillEnricher.return_value = 0
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
