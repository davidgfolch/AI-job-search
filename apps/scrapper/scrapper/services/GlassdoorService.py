import re
from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.findLastDuplicated import find_last_duplicated
from commonlib.observability import get_logger
from commonlib.terminalColor import green, cyan
from ..core.baseScrapper import htmlToMarkdown, validate, debug as baseDebug
from ..util.persistence_manager import PersistenceManager
from .BaseService import BaseService

logger = get_logger("scrapper.GlassdoorService")

class GlassdoorService(BaseService):
    def __init__(self, mysql: MysqlUtil, persistence_manager: PersistenceManager, debug: bool):
        super().__init__(mysql, persistence_manager, 'Glassdoor', debug)

    def get_job_id(self, url: str) -> str:
        # https://www.glassdoor.es/job-listing/telecom-support-engineer-...&jobListingId=1009552660667...
        return re.sub(r'.*[?&](jl|jobListingId)=([0-9]+).*', r'\2', url, flags=re.I)

    def process_job(self, title, company, location, url, html, easy_apply):
        try:
            job_id = self.get_job_id(url)
            md = htmlToMarkdown(html)
            
            logger.info("glassdoor.job.scraped", job_id=job_id, title=title, company=company, location=location, easy_apply=easy_apply,
                          console=f'{job_id}, {title}, {cyan(company)}, {location}, easy_apply={easy_apply} - ', end="")

            if validate(title, url, company, md, self.debug):
                duplicated_id = find_last_duplicated(self.mysql, title, company)
                if id := self.mysql.insert((job_id, title, company, location, None, url, md,
                                       easy_apply, self.web_page, duplicated_id)):
                    logger.info("glassdoor.job.inserted", job_id=job_id, insert_id=id, console=green(f'INSERTED {id}!'), end="")
                    if duplicated_id:
                        logger.info("glassdoor.job.duplicated", job_id=job_id, duplicated_id=duplicated_id, console=cyan(f' DUPLICATED {duplicated_id}'), end="")
                    return True
            else:
                raise ValueError('Validation failed')
            return False
        except (ValueError, KeyboardInterrupt) as e:
            raise e
        except Exception:
            baseDebug(self.debug, exception=True)
            return False
