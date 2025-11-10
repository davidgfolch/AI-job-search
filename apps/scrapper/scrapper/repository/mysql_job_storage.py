from typing import Dict, Any, Optional
from ..interfaces.job_storage_interface import JobStorageInterface
from commonlib.mysqlUtil import MysqlUtil
from commonlib.mergeDuplicates import getSelect, mergeDuplicatedJobs

class MySQLJobStorage(JobStorageInterface):
    def __init__(self, mysqlUtil: MysqlUtil):
        self.mysql = mysqlUtil

    def jobExists(self, jobId: str) -> bool:
        return self.mysql.jobExists(jobId)

    def saveJob(self, jobData: Dict[str, Any]) -> Optional[int]:
        return self.mysql.insertJob(jobData)

    def mergeDuplicates(self) -> None:
        try:
            mergeDuplicatedJobs(self.mysql, getSelect())
        except Exception as e:
            print(f"Error merging duplicates: {e}")