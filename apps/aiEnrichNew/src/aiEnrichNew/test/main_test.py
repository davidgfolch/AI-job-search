import unittest
from unittest.mock import MagicMock, patch
from ..main import run


class TestMain(unittest.TestCase):
    @patch("aiEnrichNew.main.getEnvBool")
    @patch("aiEnrichNew.main.FastCVMatcher")
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
        mock_cvMatcherClass,
        mock_getEnvBool,
    ):
        mock_getEnvBool.return_value = True
        mock_cvMatcher = mock_cvMatcherClass.instance.return_value
        mock_cvMatcher.process_db_jobs.return_value = 0
        mock_skillEnricher.return_value = 0
        mock_retry_failed_jobs.return_value = 0
        mock_dataExtractor.side_effect = [0, Exception("BreakLoop")]
        try:
            run()
        except Exception as e:
            if str(e) != "BreakLoop":
                raise e
        mock_getEnvBool.assert_called_with("AI_CV_MATCH")
        mock_cvMatcherClass.instance.assert_called_once()
        mock_cvMatcher.process_db_jobs.assert_called_once()
        mock_skillEnricher.assert_called_once()
        mock_retry_failed_jobs.assert_called_once()
        mock_consoleTimer.assert_any_call("All jobs enriched. ", "10s", end="\r")

    @patch("aiEnrichNew.main.getEnvBool")
    @patch("aiEnrichNew.main.FastCVMatcher")
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
        mock_cvMatcherClass,
        mock_getEnvBool,
    ):
        mock_getEnvBool.return_value = False
        mock_skillEnricher.return_value = 0
        mock_retry_failed_jobs.return_value = 0
        mock_dataExtractor.side_effect = [0, Exception("BreakLoop")]
        try:
            run()
        except Exception as e:
            if str(e) != "BreakLoop":
                raise e
        mock_getEnvBool.assert_called_with("AI_CV_MATCH")
        mock_cvMatcherClass.instance.assert_not_called()
        mock_skillEnricher.assert_called_once()
        mock_retry_failed_jobs.assert_called_once()
        mock_consoleTimer.assert_any_call("All jobs enriched. ", "10s", end="\r")

    @patch("aiEnrichNew.main.getEnvBool")
    @patch("aiEnrichNew.main.FastCVMatcher")
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
        mock_cvMatcherClass,
        mock_getEnvBool,
    ):
        mock_getEnvBool.return_value = False
        mock_dataExtractor.side_effect = [1, Exception("BreakLoop")]
        try:
            run()
        except Exception as e:
            if str(e) != "BreakLoop":
                raise e
        mock_skillEnricher.assert_not_called()
        mock_retry_failed_jobs.assert_not_called()
        mock_consoleTimer.assert_not_called()

    @patch("aiEnrichNew.main.getEnvBool")
    @patch("aiEnrichNew.main.FastCVMatcher")
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
        mock_cvMatcherClass,
        mock_getEnvBool,
    ):
        mock_getEnvBool.return_value = False
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

    @patch("aiEnrichNew.main.getEnvBool")
    @patch("aiEnrichNew.main.FastCVMatcher")
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
        mock_cvMatcherClass,
        mock_getEnvBool,
    ):
        mock_getEnvBool.return_value = False
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
