from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class JobStorageInterface(ABC):
    """Interface for job storage operations following DIP"""
    
    @abstractmethod
    def jobExists(self, jobId: str) -> bool:
        pass
    
    @abstractmethod
    def saveJob(self, jobData: Dict[str, Any]) -> Optional[int]:
        pass
    
    @abstractmethod
    def mergeDuplicates(self) -> None:
        pass