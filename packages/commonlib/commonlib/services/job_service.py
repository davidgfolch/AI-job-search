from typing import Dict, List, Optional
from ..repository.job_repository import JobRepository, Job

class JobService:
    """Job service handling business logic"""
    
    def __init__(self, job_repository: JobRepository):
        self.job_repository = job_repository
    
    def get_job_by_id(self, job_id: int) -> Optional[Job]:
        """Get job by ID with business validation"""
        if job_id <= 0:
            raise ValueError("Job ID must be positive")
        return self.job_repository.find_by_id(job_id)
    
    def search_jobs(self, filters: Dict[str, any] = None) -> List[Job]:
        """Search jobs with filters"""
        return self.job_repository.find_all(filters)
    
    def get_job_count(self, filters: Dict[str, any] = None) -> int:
        """Get job count with filters"""
        return self.job_repository.count(filters)
    
    def delete_job(self, job_id: int) -> bool:
        """Delete job with validation"""
        if job_id <= 0:
            raise ValueError("Job ID must be positive")
        
        job = self.job_repository.find_by_id(job_id)
        if not job:
            return False
            
        return self.job_repository.delete(job_id)
    
    def update_job_status(self, job_id: int, status_fields: Dict[str, any]) -> bool:
        """Update job status fields"""
        job = self.job_repository.find_by_id(job_id)
        if not job:
            return False
        
        # Business logic for status updates
        valid_status_fields = {'applied', 'discarded', 'flagged', 'seen', 'interested'}
        for field in status_fields:
            if field not in valid_status_fields:
                raise ValueError(f"Invalid status field: {field}")
        
        # Update logic would go here
        return True