import re
from commonlib.mysqlUtil import MysqlUtil
from commonlib.mergeDuplicates import mergeDuplicatedJobs
from commonlib.terminalColor import green
from ..core.baseScrapper import htmlToMarkdown, validate, debug as baseDebug
from ..util.persistence_manager import PersistenceManager
from .BaseService import BaseService

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
            
            print(f'{job_id}, {title}, {company}, {location}, easy_apply={easy_apply} - ', end='')
            
            if validate(title, url, company, md, self.debug):
                if id := self.mysql.insert((job_id, title, company, location, url, md,
                                       easy_apply, self.web_page)):
                    print(green(f'INSERTED {id}!'), end='')
                    mergeDuplicatedJobs(self.mysql)
                    return True
            else:
                raise ValueError('Validation failed')
            return False
        except (ValueError, KeyboardInterrupt) as e:
            raise e
        except Exception:
            baseDebug(self.debug, exception=True)
            return False
