import pytest
from unittest.mock import MagicMock, patch
from scrapper.services.scrapping_service import ScrappingService

class TestScrappingService:
    @pytest.fixture
    def mockScrapper(self):
        scrapper = MagicMock()
        scrapper.getSiteName.return_value = 'TestSite'
        scrapper.login.return_value = True
        scrapper.searchJobs.return_value = []
        return scrapper
    
    @pytest.fixture
    def mockStorage(self):
        storage = MagicMock()
        storage.jobExists.return_value = False
        storage.saveJob.return_value = 1
        storage.mergeDuplicates.return_value = None
        return storage
    
    @pytest.fixture
    def mockSelenium(self):
        return MagicMock()
    
    @pytest.fixture
    def service(self, mockScrapper, mockStorage):
        return ScrappingService(mockScrapper, mockStorage)
    
    def test_initialization(self, mockScrapper, mockStorage):
        service = ScrappingService(mockScrapper, mockStorage)
        assert service.scrapper == mockScrapper
        assert service.storage == mockStorage
    
    def test_executeScrapping_login_success(self, service, mockScrapper, mockSelenium):
        if hasattr(mockScrapper, 'login_success'):
            delattr(mockScrapper, 'login_success')
        result = service.executeScrapping(mockSelenium, ['python'], preloadOnly=False)
        assert result['site'] == 'TestSite'
        assert result['login_success'] is True
        mockScrapper.login.assert_called_once_with(mockSelenium)
    
    def test_executeScrapping_login_failure(self, service, mockScrapper, mockSelenium):
        if hasattr(mockScrapper, 'login_success'):
            delattr(mockScrapper, 'login_success')
        mockScrapper.login.return_value = False
        result = service.executeScrapping(mockSelenium, ['python'], preloadOnly=False)
        assert result['login_success'] is False
        assert result['total_processed'] == 0
        mockScrapper.searchJobs.assert_not_called()
    
    def test_executeScrapping_already_logged_in(self, service, mockScrapper, mockSelenium):
        mockScrapper.login_success = True
        result = service.executeScrapping(mockSelenium, ['python'], preloadOnly=False)
        assert result['login_success'] is True
        mockScrapper.login.assert_not_called()
    
    def test_executeScrapping_single_keyword(self, service, mockScrapper, mockStorage, mockSelenium):
        jobData = {
            'job_id': '123',
            'title': 'Developer',
            'company': 'Tech',
            'url': 'http://test.com',
            'markdown': '# Job'
        }
        mockScrapper.searchJobs.return_value = [jobData]
        result = service.executeScrapping(mockSelenium, ['python'], preloadOnly=False)
        assert result['total_processed'] == 1
        assert result['total_saved'] == 1
        assert result['total_duplicates'] == 0
        mockStorage.saveJob.assert_called_once_with(jobData)
    
    def test_executeScrapping_multiple_keywords(self, service, mockScrapper, mockStorage, mockSelenium):
        jobData1 = {'job_id': '1', 'title': 'Dev1', 'company': 'C1', 'url': 'http://1', 'markdown': '#1'}
        jobData2 = {'job_id': '2', 'title': 'Dev2', 'company': 'C2', 'url': 'http://2', 'markdown': '#2'}
        mockScrapper.searchJobs.side_effect = [[jobData1], [jobData2]]
        result = service.executeScrapping(mockSelenium, ['python', 'java'], preloadOnly=False)
        assert result['total_processed'] == 2
        assert result['total_saved'] == 2
        assert mockScrapper.searchJobs.call_count == 2
    
    def test_executeScrapping_duplicate_job(self, service, mockScrapper, mockStorage, mockSelenium):
        jobData = {'job_id': '123', 'title': 'Dev', 'company': 'C', 'url': 'http://t', 'markdown': '#'}
        mockScrapper.searchJobs.return_value = [jobData]
        mockStorage.jobExists.return_value = True
        result = service.executeScrapping(mockSelenium, ['python'], preloadOnly=False)
        assert result['total_processed'] == 1
        assert result['total_saved'] == 0
        assert result['total_duplicates'] == 1
        mockStorage.saveJob.assert_not_called()
    
    def test_executeScrapping_save_failure(self, service, mockScrapper, mockStorage, mockSelenium):
        jobData = {'job_id': '123', 'title': 'Dev', 'company': 'C', 'url': 'http://t', 'markdown': '#'}
        mockScrapper.searchJobs.return_value = [jobData]
        mockStorage.saveJob.return_value = None
        result = service.executeScrapping(mockSelenium, ['python'], preloadOnly=False)
        assert result['total_processed'] == 1
        assert result['total_saved'] == 0
        assert len(result['errors']) == 1
    
    def test_executeScrapping_missing_required_field(self, service, mockScrapper, mockSelenium):
        jobData = {'job_id': '123', 'title': ''}
        mockScrapper.searchJobs.return_value = [jobData]
        result = service.executeScrapping(mockSelenium, ['python'], preloadOnly=False)
        assert result['total_saved'] == 0
        assert len(result['errors']) == 1
    
    def test_executeScrapping_exception_in_keywords(self, service, mockScrapper, mockSelenium):
        mockScrapper.searchJobs.side_effect = Exception('Search error')
        result = service.executeScrapping(mockSelenium, ['python'], preloadOnly=False)
        assert len(result['errors']) == 1
        assert 'Search error' in result['errors'][0]
    
    def test_executeScrapping_critical_exception(self, service, mockScrapper, mockSelenium):
        if hasattr(mockScrapper, 'login_success'):
            delattr(mockScrapper, 'login_success')
        mockScrapper.login.side_effect = Exception('Critical error')
        result = service.executeScrapping(mockSelenium, ['python'], preloadOnly=False)
        assert len(result['errors']) == 1
        assert 'Critical error' in result['errors'][0]
    
    def test_executeScrapping_calls_merge_duplicates(self, service, mockStorage, mockSelenium):
        service.executeScrapping(mockSelenium, ['python'], preloadOnly=False)
        mockStorage.mergeDuplicates.assert_called_once()
    
    def test_isDuplicateJob_no_job_id(self, service):
        jobData = {'title': 'Developer'}
        result = service._isDuplicateJob(jobData)
        assert result is False
    
    def test_isDuplicateJob_exists(self, service, mockStorage):
        jobData = {'job_id': '123'}
        mockStorage.jobExists.return_value = True
        result = service._isDuplicateJob(jobData)
        assert result is True
        mockStorage.jobExists.assert_called_once_with('123')
    
    def test_saveJob_missing_fields(self, service):
        jobData = {'job_id': '123'}
        result = service._saveJob(jobData)
        assert result is False
    
    def test_saveJob_exception(self, service, mockStorage):
        jobData = {'job_id': '1', 'title': 'D', 'company': 'C', 'url': 'u', 'markdown': 'm'}
        mockStorage.saveJob.side_effect = Exception('Save error')
        result = service._saveJob(jobData)
        assert result is False

    def test_executeScrapping_with_persistence(self, service, mockScrapper, mockSelenium):
        mockPersistence = MagicMock()
        mockPersistence.get_state.return_value = {}
        result = service.executeScrapping(mockSelenium, ['python'], preloadOnly=False, persistenceManager=mockPersistence)
        mockPersistence.get_state.assert_called_once()
