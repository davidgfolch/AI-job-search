from typing import Dict, Any, Callable
from ..repository.job_repository import JobRepository
from ..services.job_service import JobService
from ..mysqlUtil import getConnection, MysqlUtil

class DependencyContainer:
    """Simple dependency injection container"""
    
    def __init__(self, mysql_connection=None):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        if mysql_connection:
            self._services['mysql_connection'] = mysql_connection
        self._setup_factories()
    
    def _setup_factories(self):
        """Setup service factories"""
        self._factories['mysql_connection'] = lambda: getConnection()
        self._factories['mysql_util'] = lambda: MysqlUtil(self.get('mysql_connection'))
        self._factories['job_repository'] = lambda: JobRepository(self.get('mysql_util'))
        self._factories['job_service'] = lambda: JobService(self.get('job_repository'))
    
    def get(self, service_name: str) -> Any:
        """Get service instance (singleton)"""
        if service_name not in self._services:
            if service_name not in self._factories:
                raise ValueError(f"Service '{service_name}' not registered")
            self._services[service_name] = self._factories[service_name]()
        return self._services[service_name]
    
    def register(self, service_name: str, factory: Callable) -> None:
        """Register a service factory"""
        self._factories[service_name] = factory
    
    def register_instance(self, service_name: str, instance: Any) -> None:
        """Register a service instance"""
        self._services[service_name] = instance