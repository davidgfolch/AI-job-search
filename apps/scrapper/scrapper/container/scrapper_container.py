from typing import Dict, Any, Callable
from ..scrappers.linkedin_scrapper import LinkedInScrapper
from ..repository.mysql_job_storage import MySQLJobStorage
from ..services.scrapping_service import ScrappingService
from commonlib.mysqlUtil import MysqlUtil

class ScrapperContainer:
    """Dependency injection container for scrapper module"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._setup_factories()
    
    def _setup_factories(self):
        """Setup service factories"""
        self._factories['mysql_util'] = lambda: MysqlUtil()
        self._factories['mysql_job_storage'] = lambda: MySQLJobStorage(self.get('mysql_util'))
        self._factories['linkedin_scrapper'] = lambda: LinkedInScrapper()
        self._factories['scrapping_service'] = lambda scrapper_name='linkedin': ScrappingService(
            self.get(f'{scrapper_name}_scrapper'),
            self.get('mysql_job_storage')
        )
    
    def get(self, service_name: str) -> Any:
        """Get service instance (singleton)"""
        if service_name not in self._services:
            if service_name not in self._factories:
                raise ValueError(f"Service '{service_name}' not registered")
            self._services[service_name] = self._factories[service_name]()
        return self._services[service_name]
    
    def get_scrapping_service(self, scrapper_name: str) -> ScrappingService:
        """Get scrapping service for specific scrapper"""
        return ScrappingService(
            self.get(f'{scrapper_name}_scrapper'),
            self.get('mysql_job_storage')
        )
    
    def register_scrapper(self, name: str, scrapper_class):
        """Register a new scrapper"""
        self._factories[f'{name}_scrapper'] = lambda: scrapper_class()