from typing import Dict, List, Optional, Any
import streamlit as st
from pandas import DataFrame
from commonlib.services.job_service import JobService
from commonlib.repository.job_repository import Job

class JobController:
    """Controller handling job-related UI operations"""
    
    def __init__(self, job_service: JobService):
        self.job_service = job_service
    
    def display_job_list(self, filters: Dict[str, any] = None) -> DataFrame:
        """Display job list with filters"""
        try:
            jobs = self.job_service.search_jobs(filters)
            return self._jobs_to_dataframe(jobs)
        except Exception as e:
            st.error(f"Error loading jobs: {e}")
            return DataFrame()
    
    def display_job_details(self, job_id: int) -> Optional[Job]:
        """Display job details"""
        try:
            job = self.job_service.get_job_by_id(job_id)
            if not job:
                st.warning("Job not found")
                return None
            return job
        except ValueError as e:
            st.error(f"Invalid job ID: {e}")
            return None
        except Exception as e:
            st.error(f"Error loading job: {e}")
            return None
    
    def update_job_status(self, job_id: int, status_fields: Dict[str, any]) -> bool:
        """Update job status"""
        try:
            success = self.job_service.update_job_status(job_id, status_fields)
            if success:
                st.success("Job updated successfully")
            else:
                st.error("Failed to update job")
            return success
        except ValueError as e:
            st.error(f"Validation error: {e}")
            return False
        except Exception as e:
            st.error(f"Error updating job: {e}")
            return False
    
    def get_job_data_dict(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get job data as dictionary for existing UI compatibility"""
        job = self.display_job_details(job_id)
        if not job:
            return None
        return self._job_to_dict(job)
    
    def get_total_job_count(self) -> int:
        """Get total job count for existing UI"""
        return self.get_job_count()
    
    def _job_to_dict(self, job: Job) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {attr: getattr(job, attr, None) for attr in dir(job) if not attr.startswith('_')}
    
    def _jobs_to_dataframe(self, jobs: List[Job]) -> DataFrame:
        """Convert jobs to DataFrame for display"""
        if not jobs:
            return DataFrame()
        
        data = []
        for job in jobs:
            data.append({
                'id': getattr(job, 'id', None),
                'title': getattr(job, 'title', ''),
                'company': getattr(job, 'company', ''),
                'location': getattr(job, 'location', ''),
                'salary': getattr(job, 'salary', ''),
                'created': getattr(job, 'created', None)
            })
        
        return DataFrame(data)