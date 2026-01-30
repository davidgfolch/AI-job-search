import unittest
from unittest.mock import MagicMock, patch
from ..main import run

class TestMain(unittest.TestCase):

    @patch('aiEnrichNew.main.getEnvBool')
    @patch('aiEnrichNew.main.FastCVMatcher')
    @patch('aiEnrichNew.main.dataExtractor')
    @patch('aiEnrichNew.main.skillEnricher')
    @patch('aiEnrichNew.main.retry_failed_jobs')
    @patch('aiEnrichNew.main.consoleTimer')
    @patch('aiEnrichNew.main.printHR')
    @patch('aiEnrichNew.main.cyan', side_effect=lambda x: x)
    @patch('time.sleep') # To prevent actual sleeping if any
    def test_run_cv_match_enabled(self, mock_sleep, mock_cyan, mock_printHR, mock_consoleTimer, mock_retry_failed_jobs, mock_skillEnricher, mock_dataExtractor, mock_cvMatcherClass, mock_getEnvBool):
        # Setup
        mock_getEnvBool.return_value = True
        mock_cvMatcher = mock_cvMatcherClass.instance.return_value
        mock_cvMatcher.process_db_jobs.return_value = 0
        mock_skillEnricher.return_value = 0
        mock_retry_failed_jobs.return_value = 0
        
        # Mock dataExtractor to return 0 (success) once, then side effect to stop loop
        # We need to break the infinite loop. run() has `while True`.
        # We can raise an exception from dataExtractor after the first call to break the loop for testing.
        mock_dataExtractor.side_effect = [0, Exception("BreakLoop")]
        
        try:
            run()
        except Exception as e:
            if str(e) != "BreakLoop":
                raise e

        # Verify
        mock_getEnvBool.assert_called_with('AI_CV_MATCH')
        mock_cvMatcherClass.instance.assert_called_once()
        mock_cvMatcher.process_db_jobs.assert_called_once()
        mock_skillEnricher.assert_called_once()
        mock_retry_failed_jobs.assert_called_once()
        # Check that consoleTimer was called for enriched & matched
        mock_consoleTimer.assert_any_call('All jobs enriched. ', '10s', end='\r')

    @patch('aiEnrichNew.main.getEnvBool')
    @patch('aiEnrichNew.main.FastCVMatcher')
    @patch('aiEnrichNew.main.dataExtractor')
    @patch('aiEnrichNew.main.skillEnricher')
    @patch('aiEnrichNew.main.retry_failed_jobs')
    @patch('aiEnrichNew.main.consoleTimer')
    @patch('aiEnrichNew.main.printHR')
    @patch('aiEnrichNew.main.cyan', side_effect=lambda x: x)
    def test_run_cv_match_disabled(self, mock_cyan, mock_printHR, mock_consoleTimer, mock_retry_failed_jobs, mock_skillEnricher, mock_dataExtractor, mock_cvMatcherClass, mock_getEnvBool):
        # Setup
        mock_getEnvBool.return_value = False
        mock_skillEnricher.return_value = 0
        mock_retry_failed_jobs.return_value = 0
        
        # Mock dataExtractor to return something other than 0 to skip the if block, 
        # or return 0 but since cvMatcher is None it won't be used.
        # Let's return 0 first, then break loop
        mock_dataExtractor.side_effect = [0, Exception("BreakLoop")]

        try:
            run()
        except Exception as e:
            if str(e) != "BreakLoop":
                raise e

        # Verify
        mock_getEnvBool.assert_called_with('AI_CV_MATCH')
        mock_cvMatcherClass.instance.assert_not_called()
        mock_skillEnricher.assert_called_once()
        mock_retry_failed_jobs.assert_called_once()
        
        # Should NOT call process_db_jobs
        # (Since we don't have a cvMatcher instance to check against, we implicitly verify by flow)
        
        # Check that consoleTimer was called for just enriched (since loop continues or not)
        # Actually logic is: if dataExtractor()==0: if cvMatcher... else...
        # If cvMatcher is None, it falls through to printHR and consoleTimer('All jobs enriched. ')
        mock_consoleTimer.assert_any_call('All jobs enriched. ', '10s', end='\r')

    @patch('aiEnrichNew.main.getEnvBool')
    @patch('aiEnrichNew.main.FastCVMatcher')
    @patch('aiEnrichNew.main.dataExtractor')
    @patch('aiEnrichNew.main.skillEnricher')
    @patch('aiEnrichNew.main.retry_failed_jobs')
    @patch('aiEnrichNew.main.consoleTimer')
    @patch('aiEnrichNew.main.printHR')
    @patch('aiEnrichNew.main.cyan', side_effect=lambda x: x)
    def test_run_data_extractor_nonzero(self, mock_cyan, mock_printHR, mock_consoleTimer, mock_retry_failed_jobs, mock_skillEnricher, mock_dataExtractor, mock_cvMatcherClass, mock_getEnvBool):
        # Setup
        mock_getEnvBool.return_value = False
        
        # Mock dataExtractor to return 1 (non-zero)
        mock_dataExtractor.side_effect = [1, Exception("BreakLoop")]

        try:
            run()
        except Exception as e:
            if str(e) != "BreakLoop":
                raise e

        # Verify
        # If dataExtractor != 0, it skips the other calls and "continues" loop (which hits BreakLoop)
        # So mocks shouldn't be called
        mock_skillEnricher.assert_not_called()
        mock_retry_failed_jobs.assert_not_called()
        mock_consoleTimer.assert_not_called()

if __name__ == '__main__':
    unittest.main()
