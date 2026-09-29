from typing import Tuple
from commonlib.sql.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from commonlib.findLastDuplicated import find_last_duplicated
from commonlib.observability import get_logger
from ..core.baseScrapper import htmlToMarkdown, validate, debug as baseDebug
from ..util.persistence_manager import PersistenceManager
from .BaseService import BaseService

logger = get_logger("scrapper.TecnoempleoService")

class TecnoempleoService(BaseService):
    def __init__(self, mysql: MysqlUtil, persistence_manager: PersistenceManager, debug: bool):
        super().__init__(mysql, persistence_manager, 'Tecnoempleo', debug)

    def get_job_id(self, url: str) -> str:
        # https://www.tecnoempleo.com/integration-specialist-gstock-web-app/php-mysql-git-symfony-api-etl-sql-ja/rf-b14e1d3282dea3a42b40
        return url.split('/')[-1]

    def process_job(self, title, company, location, url, html):
        try:
            job_id = self.get_job_id(url)
            md = htmlToMarkdown(html)
            easyApply = False

            logger.debug("tecnoempleo.job.scraped", job_id=job_id, title=title, company=company, location=location, easy_apply=easyApply)

            if validate(title, url, company, md, self.debug):
                duplicated_id = find_last_duplicated(self.mysql, title, company)
                if id := self.mysql.insert((job_id, title, company, location, None, url, md, easyApply, self.web_page, duplicated_id)):
                    logger.info("tecnoempleo.job.inserted", job_id=job_id, insert_id=id)
                    if duplicated_id:
                        logger.info("tecnoempleo.job.duplicated", job_id=job_id, duplicated_id=duplicated_id)
                    return True
            else:
                raise ValueError('Validation failed')
            return False
        except (ValueError, KeyboardInterrupt) as e:
            raise e
        except Exception:
            baseDebug(self.debug, exception=True)
            return False
