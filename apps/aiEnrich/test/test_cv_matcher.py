import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import pandas as pd

from aiEnrich.cvMatcher import (
    cvMatch, save, loadCVContent, extractTextFromPDF, 
    getJobIdsList, CVMatcher
)


class TestCVMatcher:
    @patch('aiEnrich.cvMatcher.getEnvBool')
    def test_cv_match_disabled(self, mock_get_env_bool):
        mock_get_env_bool.return_value = False
        result = cvMatch()
        assert result == 0

    @patch('aiEnrich.cvMatcher.getEnvBool')
    @patch('aiEnrich.cvMatcher.loadCVContent')
    def test_cv_match_cv_not_loaded(self, mock_load_cv, mock_get_env_bool):
        mock_get_env_bool.return_value = True
        mock_load_cv.return_value = False
        result = cvMatch()
        assert result == 0

    @patch('aiEnrich.cvMatcher.getEnvBool')
    @patch('aiEnrich.cvMatcher.loadCVContent')
    @patch('aiEnrich.cvMatcher.MysqlUtil')
    def test_cv_match_no_jobs(self, mock_mysql_util, mock_load_cv, mock_get_env_bool):
        mock_get_env_bool.return_value = True
        mock_load_cv.return_value = True
        
        mock_mysql = MagicMock()
        mock_mysql.count.return_value = 0
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        result = cvMatch()
        assert result == 0

    @patch('aiEnrich.cvMatcher.getEnvBool')
    @patch('aiEnrich.cvMatcher.loadCVContent')
    @patch('aiEnrich.cvMatcher.MysqlUtil')
    @patch('aiEnrich.cvMatcher.CVMatcher')
    @patch('aiEnrich.cvMatcher.getJobIdsList')
    def test_cv_match_success(self, mock_get_job_ids, mock_cv_matcher_class, 
                             mock_mysql_util, mock_load_cv, mock_get_env_bool):
        mock_get_env_bool.return_value = True
        mock_load_cv.return_value = True
        
        mock_mysql = MagicMock()
        mock_mysql.count.return_value = 1
        mock_mysql.fetchOne.return_value = (1, 'Test Job', 'Job description', 'Test Company')
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        mock_get_job_ids.return_value = [1]
        
        mock_crew = MagicMock()
        mock_crew_output = MagicMock()
        mock_crew_output.raw = '{"cv_match_percentage": 85}'
        mock_crew.kickoff.return_value = mock_crew_output
        mock_cv_matcher_class.return_value.crew.return_value = mock_crew
        
        with patch('aiEnrich.cvMatcher.combineTaskResults', return_value={'cv_match_percentage': 85}), \
             patch('aiEnrich.cvMatcher.save'), \
             patch('aiEnrich.cvMatcher.mapJob', return_value=('Test Job', 'Test Company', 'Job description')), \
             patch('aiEnrich.cvMatcher.printJob'), \
             patch('aiEnrich.cvMatcher.printHR'), \
             patch('aiEnrich.cvMatcher.footer'), \
             patch('aiEnrich.cvMatcher.StopWatch'), \
             patch('aiEnrich.cvMatcher.cvContent', 'CV content'):
            
            result = cvMatch()
            assert result == 1

    def test_save(self):
        mock_mysql = MagicMock()
        result = {'cv_match_percentage': 85}
        
        with patch('aiEnrich.cvMatcher.validateResult'), \
             patch('aiEnrich.cvMatcher.maxLen', return_value=(85, 1)), \
             patch('aiEnrich.cvMatcher.emptyToNone', return_value=(85, 1)):
            
            save(mock_mysql, 1, result)
            mock_mysql.updateFromAI.assert_called_once()

    def test_get_job_ids_list(self):
        mock_mysql = MagicMock()
        mock_mysql.fetchAll.return_value = [(1,), (2,), (3,)]
        
        with patch('aiEnrich.cvMatcher.yellow'):
            result = getJobIdsList(mock_mysql)
            assert result == [1, 2, 3]

    @patch('pdfplumber.open')
    def test_extract_text_from_pdf(self, mock_pdf_open):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample text"
        mock_page.extract_tables.return_value = [
            [['Header1', 'Header2'], ['Row1Col1', 'Row1Col2']]
        ]
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf
        
        with patch.object(pd.DataFrame, 'to_markdown', return_value='| Header1 | Header2 |\n|---------|----------|\n| Row1Col1 | Row1Col2 |'):
            result = extractTextFromPDF('test.pdf')
            assert 'Sample text' in result
            assert 'Header1' in result

    @patch('aiEnrich.cvMatcher.getEnvBool')
    def test_load_cv_content_disabled(self, mock_get_env_bool):
        mock_get_env_bool.return_value = False
        result = loadCVContent()
        assert result is False

    @patch('aiEnrich.cvMatcher.CV_LOCATION', 'test.doc')
    @patch('aiEnrich.cvMatcher.getEnvBool')
    @patch('aiEnrich.cvMatcher.getEnv')
    def test_load_cv_content_invalid_format(self, mock_get_env, mock_get_env_bool):
        mock_get_env_bool.return_value = True
        mock_get_env.return_value = 'test.doc'  # Invalid format
        
        result = loadCVContent()
        assert result is False

    @patch('aiEnrich.cvMatcher.getEnvBool')
    @patch('aiEnrich.cvMatcher.getEnv')
    @patch('aiEnrich.cvMatcher.Path')
    def test_load_cv_content_file_not_found(self, mock_path, mock_get_env, mock_get_env_bool):
        mock_get_env_bool.return_value = True
        mock_get_env.return_value = 'test.pdf'
        
        mock_file_path = MagicMock()
        mock_file_path.exists.return_value = False
        mock_file_path.suffix.lower.return_value = '.pdf'
        mock_path.return_value = mock_file_path
        
        result = loadCVContent()
        assert result is False

    @patch('aiEnrich.cvMatcher.getEnvBool')
    @patch('aiEnrich.cvMatcher.getEnv')
    @patch('aiEnrich.cvMatcher.Path')
    @patch('builtins.open', new_callable=mock_open, read_data='CV content')
    def test_load_cv_content_txt_success(self, mock_file, mock_path, mock_get_env, mock_get_env_bool):
        mock_get_env_bool.return_value = True
        mock_get_env.return_value = 'test.pdf'
        
        # Mock PDF path doesn't exist, but TXT path exists
        mock_pdf_path = MagicMock()
        mock_pdf_path.exists.return_value = False
        mock_pdf_path.suffix.lower.return_value = '.pdf'
        
        mock_txt_path = MagicMock()
        mock_txt_path.exists.return_value = True
        
        mock_path.side_effect = [mock_pdf_path, mock_txt_path]
        
        with patch('aiEnrich.cvMatcher.cvContent', None):
            result = loadCVContent()
            assert result is True

    @patch('aiEnrich.cvMatcher.CV_LOCATION', 'test.pdf')
    @patch('aiEnrich.cvMatcher.getEnvBool')
    @patch('aiEnrich.cvMatcher.getEnv')
    @patch('aiEnrich.cvMatcher.Path')
    @patch('aiEnrich.cvMatcher.extractTextFromPDF')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_cv_content_pdf_success(self, mock_file, mock_extract_pdf, 
                                        mock_path, mock_get_env, mock_get_env_bool):
        mock_get_env_bool.return_value = True
        mock_get_env.return_value = 'test.pdf'
        mock_extract_pdf.return_value = 'Extracted PDF content'
        
        # Mock PDF path exists, TXT path doesn't exist
        mock_pdf_path = MagicMock()
        mock_pdf_path.exists.return_value = True
        mock_pdf_path.suffix.lower.return_value = '.pdf'
        
        mock_txt_path = MagicMock()
        mock_txt_path.exists.return_value = False
        
        mock_path.side_effect = [mock_pdf_path, mock_txt_path]
        
        with patch('aiEnrich.cvMatcher.cvContent', None):
            result = loadCVContent()
            assert result is True
            mock_extract_pdf.assert_called_once_with('test.pdf')

    def test_cv_matcher_class_initialization(self):
        matcher = CVMatcher()
        # The config files are loaded as dictionaries, not file paths
        assert isinstance(matcher.agents_config, dict)
        assert isinstance(matcher.tasks_config, dict)

    @patch('aiEnrich.cvMatcher.Agent')
    @patch('aiEnrich.cvMatcher.getEnv')
    def test_cv_matcher_agent(self, mock_get_env, mock_agent):
        mock_get_env.return_value = '300'
        matcher = CVMatcher()
        matcher.agents_config = {'cv_matcher_agent': {'role': 'CV Matcher'}}
        
        agent = matcher.cv_matcher_agent()
        mock_agent.assert_called_once()

    @patch('aiEnrich.cvMatcher.Task')
    def test_cv_matcher_task(self, mock_task):
        matcher = CVMatcher()
        matcher.tasks_config = {'cv_matcher_task': {'description': 'Match CV'}}
        
        task = matcher.cv_matcher_task()
        mock_task.assert_called_once()

    @patch('aiEnrich.cvMatcher.Crew')
    def test_cv_matcher_crew(self, mock_crew):
        matcher = CVMatcher()
        
        with patch.object(matcher, 'cv_matcher_agent', return_value=MagicMock()), \
             patch.object(matcher, 'cv_matcher_task', return_value=MagicMock()):
            
            crew = matcher.crew()
            mock_crew.assert_called_once()