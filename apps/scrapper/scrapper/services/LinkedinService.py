import re
from typing import Tuple
from commonlib.sql.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, QRY_UPDATE_JOB_DIRECT_URL, MysqlUtil
from commonlib.findLastDuplicated import find_last_duplicated
from commonlib.observability import get_logger
from ..core import baseScrapper
from ..util.persistence_manager import PersistenceManager
from .BaseService import BaseService

logger = get_logger("scrapper.LinkedinService")

class LinkedinService(BaseService):
    def __init__(self, mysql: MysqlUtil, persistence_manager: PersistenceManager, debug: bool):
        super().__init__(mysql, persistence_manager, 'Linkedin', debug)

    def get_job_id(self, url: str) -> int:
        return int(re.sub(r'.*/jobs/view/([^/]+)/.*', r'\1', url))

    def get_job_url_short(self, url: str):
        return re.sub(r'(.*/jobs/view/([^/]+)/).*', r'\1', url)

    def job_exists_in_db(self, url: str) -> Tuple[int, bool]:
        # Overriding to return job_id as int if needed, or stick to base?
        # Base returns str. Here explicit int.
        jobId = self.get_job_id(url)
        return (jobId, self.mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, jobId) is not None)

    def process_job(self, title, company, location, url, html, is_direct_url_scrapping: bool, easy_apply: bool):
        try:
            url_short = self.get_job_url_short(url)
            jobId = self.get_job_id(url_short)
            md = baseScrapper.htmlToMarkdown(html)
            logger.debug("linkedin.job.scraped", job_id=jobId, title=title, company=company, location=location, easy_apply=easy_apply)
            if baseScrapper.validate(title, url_short, company, md, self.debug):
                if is_direct_url_scrapping and self.mysql.jobExists(str(jobId)):
                    self.update_job(jobId, title, company, location, url_short, html, md, easy_apply)
                else:
                    duplicated_id = find_last_duplicated(self.mysql, title, company)
                    if id := self.mysql.insert((jobId, title, company, location, None, url_short, md, easy_apply, self.web_page, duplicated_id)):
                        logger.info("linkedin.job.inserted", job_id=jobId, insert_id=id)
                        if duplicated_id:
                            logger.info("linkedin.job.duplicated", job_id=jobId, duplicated_id=duplicated_id)
            else:
                raise ValueError('Validation failed')
        except (ValueError, KeyboardInterrupt) as e:
            raise e
        except Exception:
            baseScrapper.debug(self.debug, exception=True)

    def print_job(self, title, company, location, url, jobId, html, md):
        logger.debug("linkedin.job.already_exists", job_id=jobId, title=title, company=company, location=location, url=url, html_length=len(html or ''), markdown_length=len(md or ''))

    def update_job(self, jobId, title, company, location, url, html, md, easy_apply):
        self.print_job(title, company, location, url, jobId, html, md)
        params = (title, company, location, url, md, easy_apply, jobId, self.web_page)
        self.mysql.executeAndCommit(QRY_UPDATE_JOB_DIRECT_URL, params)
        logger.info("linkedin.job.updated", job_id=jobId)
