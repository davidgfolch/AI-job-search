from typing import Dict, List, Optional
from ..repository.job_repository import JobRepository, Job

class JobService:
    def __init__(self, jobRepository: JobRepository):
        self.jobRepository = jobRepository

    def getJobById(self, jobId: int) -> Optional[Job]:
        if jobId <= 0:
            raise ValueError("Job ID must be positive")
        return self.jobRepository.findById(jobId)

    def searchJobs(self, filters: Dict[str, any] = None) -> List[Job]:
        return self.jobRepository.findAll(filters)

    def getJobCount(self, filters: Dict[str, any] = None) -> int:
        return self.jobRepository.count(filters)

    def deleteJob(self, jobId: int) -> bool:
        if jobId <= 0:
            raise ValueError("Job ID must be positive")
        job = self.jobRepository.findById(jobId)
        if not job:
            return False
        return self.jobRepository.delete(jobId)

    def updateJobStatus(self, jobId: int, statusFields: Dict[str, any]) -> bool:
        job = self.jobRepository.findById(jobId)
        if not job:
            return False
        validStatusFields = {'applied', 'discarded', 'flagged', 'seen', 'interested'}
        for field in statusFields:
            if field not in validStatusFields:
                raise ValueError(f"Invalid status field: {field}")
        return True