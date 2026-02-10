from typing import Tuple
from commonlib.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from commonlib.findLastDuplicated import find_last_duplicated
from commonlib.terminalColor import green, cyan
from ..core.baseScrapper import htmlToMarkdown, validate, debug as baseDebug
from ..util.persistence_manager import PersistenceManager
from .BaseService import BaseService

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
            
            print(f'{job_id}, {title}, {company}, {location}, easy_apply={easyApply} - ', end='')
            
            if validate(title, url, company, md, self.debug):
                duplicated_id = find_last_duplicated(self.mysql, title, company)
                if id := self.mysql.insert((job_id, title, company, location, url, md, easyApply, self.web_page, duplicated_id)):
                    print(green(f'INSERTED {id}!'), end='')
                    if duplicated_id:
                        print(cyan(f' DUPLICATED {duplicated_id}'), end="")
                    return True
            else:
                raise ValueError('Validation failed')
            return False
        except (ValueError, KeyboardInterrupt) as e:
            raise e
        except Exception:
            baseDebug(self.debug, exception=True)
            return False
