from abc import ABC, abstractmethod
from typing import Tuple
from commonlib.sql.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from commonlib.observability import get_logger
from ..util.persistence_manager import PersistenceManager

logger = get_logger("scrapper.BaseService")

class BaseService(ABC):
    def __init__(self, mysql: MysqlUtil, persistence_manager: PersistenceManager, web_page: str, debug: bool):
        self.mysql = mysql
        self.persistence_manager = persistence_manager
        self.web_page = web_page
        self.debug = debug

    @abstractmethod
    def get_job_id(self, url: str) -> str:
        """Extract job ID from URL"""
        pass

    def job_exists_in_db(self, url: str) -> Tuple[str, bool]:
        job_id = self.get_job_id(url)
        exists = self.mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, job_id) is not None
        if exists:
            logger.info("scraper.job.already_exists", job_id=job_id)
        return (job_id, exists)

    def prepare_resume(self):
        self.persistence_manager.prepare_resume(self.web_page)

    def should_skip_keyword(self, keyword: str):
        return self.persistence_manager.should_skip_keyword(keyword)

    def update_state(self, keyword: str, page: int):
        self.persistence_manager.update_state(self.web_page, keyword, page)

    def clear_state(self):
        self.persistence_manager.clear_state(self.web_page)
        
    def post_process_markdown(self, md: str) -> str:
        """Hook for post-processing markdown. Defaults to identity."""
        return md
