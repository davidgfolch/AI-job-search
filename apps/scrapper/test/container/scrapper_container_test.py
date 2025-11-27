import pytest
from unittest.mock import MagicMock, patch
from scrapper.container.scrapper_container import ScrapperContainer

class TestScrapperContainer:
    @pytest.fixture
    def container(self):
        return ScrapperContainer()
    
    def test_initialization(self, container):
        assert container is not None
    
    @patch('scrapper.container.scrapper_container.MysqlUtil')
    def test_get_mysql_util(self, mockMysqlUtil, container):
        mockInstance = MagicMock()
        mockMysqlUtil.return_value = mockInstance
        result = container.get('mysql_util')
        assert result == mockInstance
    
    @patch('scrapper.container.scrapper_container.MysqlUtil')
    def test_get_job_storage(self, mockMysqlUtil, container):
        storage = container.get('mysql_job_storage')
        assert storage is not None
        assert hasattr(storage, 'jobExists')
        assert hasattr(storage, 'saveJob')
    
    @patch('scrapper.container.scrapper_container.MysqlUtil')
    def test_get_linkedin_scrapper(self, mockMysqlUtil, container):
        with patch('scrapper.baseScrapper.getAndCheckEnvVars', 
                   return_value=('email', 'pwd', 'search')):
            scrapper = container.get('linkedin_scrapper')
            assert scrapper is not None
            assert hasattr(scrapper, 'login')
            assert hasattr(scrapper, 'searchJobs')
    
    @patch('scrapper.container.scrapper_container.MysqlUtil')
    def test_get_scrapping_service(self, mockMysqlUtil, container):
        with patch('scrapper.baseScrapper.getAndCheckEnvVars',
                   return_value=('email', 'pwd', 'search')):
            service = container.get_scrapping_service('linkedin')
            assert service is not None
            assert hasattr(service, 'executeScrapping')
    
    @patch('scrapper.container.scrapper_container.MysqlUtil')
    def test_singleton_mysql_util(self, mockMysqlUtil, container):
        mockInstance = MagicMock()
        mockMysqlUtil.return_value = mockInstance
        result1 = container.get('mysql_util')
        result2 = container.get('mysql_util')
        assert result1 == result2
        mockMysqlUtil.assert_called_once()
    
    @patch('scrapper.container.scrapper_container.MysqlUtil')
    def test_singleton_job_storage(self, mockMysqlUtil, container):
        storage1 = container.get('mysql_job_storage')
        storage2 = container.get('mysql_job_storage')
        assert storage1 == storage2
    
    @patch('scrapper.container.scrapper_container.MysqlUtil')
    def test_singleton_linkedin_scrapper(self, mockMysqlUtil, container):
        with patch('scrapper.baseScrapper.getAndCheckEnvVars',
                   return_value=('email', 'pwd', 'search')):
            scrapper1 = container.get('linkedin_scrapper')
            scrapper2 = container.get('linkedin_scrapper')
            assert scrapper1 == scrapper2
    
    @patch('scrapper.container.scrapper_container.MysqlUtil')
    def test_singleton_scrapping_service(self, mockMysqlUtil, container):
        with patch('scrapper.baseScrapper.getAndCheckEnvVars',
                   return_value=('email', 'pwd', 'search')):
            service1 = container.get_scrapping_service('linkedin')
            service2 = container.get_scrapping_service('linkedin')
            assert service1 == service2
    
    def test_get_nonexistent_service_raises_error(self, container):
        """Test that getting non-existent service raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            container.get('nonexistent_service')
        assert "Service 'nonexistent_service' not registered" in str(exc_info.value)
    
    @patch('scrapper.container.scrapper_container.MysqlUtil')
    def test_register_custom_scrapper(self, mockMysqlUtil, container):
        """Test registering a custom scrapper"""
        class CustomScrapper:
            def __init__(self):
                self.name = 'custom'
        
        container.register_scrapper('custom', CustomScrapper)
        assert 'custom_scrapper' in container._factories
        
        scrapper = container.get('custom_scrapper')
        assert isinstance(scrapper, CustomScrapper)
        assert scrapper.name == 'custom'
    
    @patch('scrapper.container.scrapper_container.MysqlUtil')
    def test_multiple_scrappers_share_storage(self, mockMysqlUtil, container):
        """Test that different scrappers share the same storage instance"""
        class CustomScrapper:
            pass
        
        with patch('scrapper.baseScrapper.getAndCheckEnvVars',
                   return_value=('email', 'pwd', 'search')):
            container.register_scrapper('custom', CustomScrapper)
            
            service1 = container.get_scrapping_service('linkedin')
            service2 = container.get_scrapping_service('custom')
            
            # Both services should share the same storage instance
            assert service1.storage is service2.storage
