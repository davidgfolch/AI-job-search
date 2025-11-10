from typing import Dict, Any, Optional
from ..interfaces.job_storage_interface import JobStorageInterface
from commonlib.mysqlUtil import MysqlUtil
from commonlib.mergeDuplicates import getSelect, mergeDuplicatedJobs

class MySQLJobStorage(JobStorageInterface):
    """MySQL implementation of job storage following DIP"""
    
    def __init__(self, mysql_util: MysqlUtil):
        self.mysql = mysql_util
    
    def job_exists(self, job_id: str) -> bool:
        """Check if job already exists in database"""
        return self.mysql.job_exists(job_id)
    
    def save_job(self, job_data: Dict[str, Any]) -> Optional[int]:
        """Save job data to MySQL database. Returns row ID if saved, None on error"""
        return self.mysql.insertJob(job_data)
    
    def merge_duplicates(self) -> None:
        """Merge duplicate jobs in database"""
        try:
            mergeDuplicatedJobs(self.mysql, getSelect())
        except Exception as e:
            print(f"Error merging duplicates: {e}")