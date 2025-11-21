import pytest
from unittest.mock import MagicMock, patch
from scrapper.repository.mysql_job_storage import MySQLJobStorage

class TestMySQLJobStorage:
    @pytest.fixture
    def mockMysql(self):
        return MagicMock()
    
    @pytest.fixture
    def storage(self, mockMysql):
        return MySQLJobStorage(mockMysql)
    
    def test_initialization(self, mockMysql):
        storage = MySQLJobStorage(mockMysql)
        assert storage.mysql == mockMysql
    
    def test_jobExists_true(self, storage, mockMysql):
        mockMysql.jobExists.return_value = True
        result = storage.jobExists('12345')
        assert result is True
        mockMysql.jobExists.assert_called_once_with('12345')
    
    def test_jobExists_false(self, storage, mockMysql):
        mockMysql.jobExists.return_value = False
        result = storage.jobExists('99999')
        assert result is False
        mockMysql.jobExists.assert_called_once_with('99999')
    
    def test_saveJob_success(self, storage, mockMysql):
        jobData = {
            'job_id': '12345',
            'title': 'Software Engineer',
            'company': 'Tech Corp',
            'url': 'https://example.com/job/12345',
            'markdown': '# Job Description'
        }
        mockMysql.insertJob.return_value = 42
        result = storage.saveJob(jobData)
        assert result == 42
        mockMysql.insertJob.assert_called_once_with(jobData)
    
    def test_saveJob_failure(self, storage, mockMysql):
        jobData = {'job_id': '12345'}
        mockMysql.insertJob.return_value = None
        result = storage.saveJob(jobData)
        assert result is None
    
    @patch('scrapper.repository.mysql_job_storage.mergeDuplicatedJobs')
    @patch('scrapper.repository.mysql_job_storage.getSelect')
    def test_mergeDuplicates_success(self, mockGetSelect, mockMergeDuplicatedJobs, storage, mockMysql):
        mockGetSelect.return_value = 'SELECT * FROM jobs'
        storage.mergeDuplicates()
        mockGetSelect.assert_called_once()
        mockMergeDuplicatedJobs.assert_called_once_with(mockMysql, 'SELECT * FROM jobs')
    
    @patch('scrapper.repository.mysql_job_storage.mergeDuplicatedJobs')
    @patch('scrapper.repository.mysql_job_storage.getSelect')
    def test_mergeDuplicates_exception(self, mockGetSelect, mockMergeDuplicatedJobs, storage, mockMysql):
        mockGetSelect.return_value = 'SELECT * FROM jobs'
        mockMergeDuplicatedJobs.side_effect = Exception('Database error')
        storage.mergeDuplicates()
        mockMergeDuplicatedJobs.assert_called_once()
