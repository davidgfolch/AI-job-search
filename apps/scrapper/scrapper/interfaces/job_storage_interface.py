from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class JobStorageInterface(ABC):
    """Interface for job storage operations following DIP"""
    
    @abstractmethod
    def job_exists(self, job_id: str) -> bool:
        """Check if job already exists in storage"""
        pass
    
    @abstractmethod
    def save_job(self, job_data: Dict[str, Any]) -> Optional[int]:
        """Save job data to storage"""
        pass
    
    @abstractmethod
    def merge_duplicates(self) -> None:
        """Merge duplicate jobs in storage"""
        pass