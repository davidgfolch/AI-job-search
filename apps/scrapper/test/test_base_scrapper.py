import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from test_helpers import BaseScrapper


class TestBaseScrapper:
    def test_initialization(self):
        scrapper = BaseScrapper()
        assert scrapper.name == "BaseScrapper"
        assert scrapper.url == ""
        assert scrapper.jobsFound == 0
        assert scrapper.jobsSaved == 0
        assert scrapper.jobsDuplicates == 0
        assert scrapper.jobsErrors == 0

    def test_initialization_with_params(self):
        scrapper = BaseScrapper("TestScrapper", "https://test.com")
        assert scrapper.name == "TestScrapper"
        assert scrapper.url == "https://test.com"

    @patch('test_helpers.MysqlUtil')
    def test_save_job_success(self, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql.insertJob.return_value = True
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        scrapper = BaseScrapper()
        job_data = {
            'title': 'Test Job',
            'company': 'Test Company',
            'url': 'https://test.com/job/1'
        }
        
        result = scrapper.saveJob(job_data)
        
        assert result is True
        assert scrapper.jobsSaved == 1
        mock_mysql.insertJob.assert_called_once_with(job_data)

    @patch('test_helpers.MysqlUtil')
    def test_save_job_duplicate(self, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql.insertJob.return_value = False
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        scrapper = BaseScrapper()
        job_data = {
            'title': 'Test Job',
            'company': 'Test Company',
            'url': 'https://test.com/job/1'
        }
        
        result = scrapper.saveJob(job_data)
        
        assert result is False
        assert scrapper.jobsDuplicates == 1

    @patch('test_helpers.MysqlUtil')
    def test_save_job_exception(self, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql.insertJob.side_effect = Exception("Database error")
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        scrapper = BaseScrapper()
        job_data = {
            'title': 'Test Job',
            'company': 'Test Company',
            'url': 'https://test.com/job/1'
        }
        
        result = scrapper.saveJob(job_data)
        
        assert result is False
        assert scrapper.jobsErrors == 1

    def test_print_stats(self):
        scrapper = BaseScrapper("TestScrapper")
        scrapper.jobsFound = 10
        scrapper.jobsSaved = 8
        scrapper.jobsDuplicates = 1
        scrapper.jobsErrors = 1
        
        with patch('test_helpers.printHR'), \
             patch('test_helpers.green') as mock_green, \
             patch('test_helpers.yellow') as mock_yellow, \
             patch('test_helpers.red') as mock_red:
            
            scrapper.printStats()
            
            # Verify that color functions are called with expected values
            mock_green.assert_called()
            mock_yellow.assert_called()
            mock_red.assert_called()

    def test_print_stats_no_jobs(self):
        scrapper = BaseScrapper("TestScrapper")
        
        with patch('test_helpers.printHR'), \
             patch('test_helpers.green') as mock_green:
            
            scrapper.printStats()
            mock_green.assert_called()

    def test_get_stats(self):
        scrapper = BaseScrapper("TestScrapper")
        scrapper.jobsFound = 5
        scrapper.jobsSaved = 3
        scrapper.jobsDuplicates = 1
        scrapper.jobsErrors = 1
        
        stats = scrapper.getStats()
        
        expected = {
            'name': 'TestScrapper',
            'jobsFound': 5,
            'jobsSaved': 3,
            'jobsDuplicates': 1,
            'jobsErrors': 1
        }
        
        assert stats == expected

    def test_increment_counters(self):
        scrapper = BaseScrapper()
        
        # Test individual increments
        scrapper.jobsFound += 1
        scrapper.jobsSaved += 1
        scrapper.jobsDuplicates += 1
        scrapper.jobsErrors += 1
        
        assert scrapper.jobsFound == 1
        assert scrapper.jobsSaved == 1
        assert scrapper.jobsDuplicates == 1
        assert scrapper.jobsErrors == 1

    @patch('test_helpers.MysqlUtil')
    def test_save_job_with_none_data(self, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        scrapper = BaseScrapper()
        
        result = scrapper.saveJob(None)
        
        assert result is False
        assert scrapper.jobsErrors == 1

    @patch('test_helpers.MysqlUtil')
    def test_save_job_with_empty_data(self, mock_mysql_util):
        mock_mysql = MagicMock()
        mock_mysql_util.return_value.__enter__.return_value = mock_mysql
        
        scrapper = BaseScrapper()
        
        result = scrapper.saveJob({})
        
        assert result is False
        assert scrapper.jobsErrors == 1