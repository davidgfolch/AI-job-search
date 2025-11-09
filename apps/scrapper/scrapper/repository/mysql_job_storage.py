from typing import Dict, Any, Optional
from ..interfaces.job_storage_interface import JobStorageInterface
from commonlib.mysqlUtil import MysqlUtil, QRY_FIND_JOB_BY_JOB_ID
from commonlib.mergeDuplicates import getSelect, mergeDuplicatedJobs

class MySQLJobStorage(JobStorageInterface):
    """MySQL implementation of job storage following DIP"""
    
    def __init__(self, mysql_util: MysqlUtil):
        self.mysql = mysql_util
    
    def job_exists(self, job_id: str) -> bool:
        """Check if job already exists in database"""
        try:
            result = self.mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, job_id)
            return result is not None
        except Exception:
            return False
    
    def save_job(self, job_data: Dict[str, Any]) -> Optional[int]:
        """Save job data to MySQL database"""
        try:
            # Extract data in the order expected by the insert query
            params = (
                job_data['job_id'],
                job_data['title'],
                job_data['company'],
                job_data.get('location', ''),
                job_data['url'],
                job_data['markdown'],
                job_data.get('easy_apply', False),
                job_data.get('web_page', 'Unknown')
            )
            
            return self.mysql.insert(params)
            
        except Exception as e:
            print(f"Error saving job to MySQL: {e}")
            return None
    
    def merge_duplicates(self) -> None:
        """Merge duplicate jobs in database"""
        try:
            mergeDuplicatedJobs(self.mysql, getSelect())
        except Exception as e:
            print(f"Error merging duplicates: {e}")