from typing import Tuple
from commonlib.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from commonlib.mergeDuplicates import getSelect, mergeDuplicatedJobs
from commonlib.terminalColor import green, yellow
from ...baseScrapper import htmlToMarkdown, validate, debug as baseDebug
from ...persistence_manager import PersistenceManager

class TecnoempleoJobService:
    def __init__(self, mysql: MysqlUtil, persistence_manager: PersistenceManager):
        self.mysql = mysql
        self.persistence_manager = persistence_manager
        self.web_page = 'Tecnoempleo'
        self.debug = False

    def set_debug(self, debug: bool):
        self.debug = debug

    def get_job_id(self, url: str) -> str:
        # https://www.tecnoempleo.com/integration-specialist-gstock-web-app/php-mysql-git-symfony-api-etl-sql-ja/rf-b14e1d3282dea3a42b40
        return url.split('/')[-1]

    def job_exists_in_db(self, url: str) -> Tuple[str, bool]:
        job_id = self.get_job_id(url)
        return (job_id, self.mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, job_id) is not None)

    def process_job(self, title, company, location, url, html):
        try:
            job_id = self.get_job_id(url)
            md = htmlToMarkdown(html)
            easyApply = False
            
            print(f'{job_id}, {title}, {company}, {location}, easy_apply={easyApply} - ', end='')
            
            if validate(title, url, company, md, self.debug):
                if id := self.mysql.insert((job_id, title, company, location, url, md, easyApply, self.web_page)):
                    print(green(f'INSERTED {id}!'), end='')
                    mergeDuplicatedJobs(self.mysql, getSelect())
                    return True
            else:
                raise ValueError('Validation failed')
            return False
        except (ValueError, KeyboardInterrupt) as e:
            raise e
        except Exception:
            baseDebug(self.debug, exception=True)
            return False

    def prepare_resume(self):
        self.persistence_manager.prepare_resume(self.web_page)

    def should_skip_keyword(self, keyword: str):
        return self.persistence_manager.should_skip_keyword(keyword)

    def update_state(self, keyword: str, page: int):
        self.persistence_manager.update_state(self.web_page, keyword, page)

    def clear_state(self):
        self.persistence_manager.clear_state(self.web_page)
