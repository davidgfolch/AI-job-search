from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..seleniumUtil import SeleniumUtil

class ScrapperInterface(ABC):
    """Interface for job scrappers following ISP"""
    
    @abstractmethod
    def login(self, selenium: SeleniumUtil) -> bool:
        """Login to the job site"""
        pass
    
    @abstractmethod
    def search_jobs(self, selenium: SeleniumUtil, keywords: str) -> List[Dict[str, Any]]:
        """Search for jobs with given keywords"""
        pass
    
    @abstractmethod
    def extract_job_data(self, selenium: SeleniumUtil, job_element) -> Dict[str, Any]:
        """Extract job data from a job element"""
        pass
    
    @abstractmethod
    def get_site_name(self) -> str:
        """Get the name of the job site"""
        pass