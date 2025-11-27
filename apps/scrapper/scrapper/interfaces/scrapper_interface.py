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
    def searchJobs(self, selenium: SeleniumUtil, keywords: str, startPage: int = 1, onPageComplete: Any = None) -> List[Dict[str, Any]]:
        """Search for jobs with given keywords"""
        pass
    
    @abstractmethod
    def extractJobData(self, selenium: SeleniumUtil, jobElement) -> Dict[str, Any]:
        """Extract job data from a job element"""
        pass
    
    @abstractmethod
    def getSiteName(self) -> str:
        """Get the name of the job site"""
        pass