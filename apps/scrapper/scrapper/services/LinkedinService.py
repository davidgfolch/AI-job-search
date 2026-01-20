import re
from typing import Tuple
from commonlib.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, QRY_UPDATE_JOB_DIRECT_URL, MysqlUtil
from commonlib.mergeDuplicates import getSelect, mergeDuplicatedJobs
from commonlib.terminalColor import green, magenta, yellow
from ..core import baseScrapper
from ..util.persistence_manager import PersistenceManager
from .BaseService import BaseService

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
            print(f'{jobId}, {title}, {company}, {location}, easy_apply={easy_apply} - ', end='', flush=True)
            if baseScrapper.validate(title, url_short, company, md, self.debug):
                if is_direct_url_scrapping and self.mysql.jobExists(str(jobId)):
                    self.update_job(jobId, title, company, location, url_short, html, md, easy_apply)
                elif id := self.mysql.insert((jobId, title, company, location, url_short, md, easy_apply, self.web_page)):
                    print(green(f'INSERTED {id}!'), end='', flush=True)
                    mergeDuplicatedJobs(self.mysql, getSelect())
            else:
                raise ValueError('Validation failed')
        except (ValueError, KeyboardInterrupt) as e:
            raise e
        except Exception:
            baseScrapper.debug(self.debug, exception=True)

    def print_job(self, title, company, location, url, jobId, html, md):
        print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'))
        print(yellow(f'TITLE={title}'))
        print(yellow(f'COMPANY={company}'))
        print(yellow(f'LOCATION={location}'))
        print(yellow(f'URL={url}'))
        print(yellow(f'HTML:\n', magenta(html)))
        print(yellow(f'MARKDOWN:\n', magenta(md)))

    def update_job(self, jobId, title, company, location, url, html, md, easy_apply):
        self.print_job(title, company, location, url, jobId, html, md)
        params = (title, company, location, url, md, easy_apply, jobId, self.web_page)
        self.mysql.executeAndCommit(QRY_UPDATE_JOB_DIRECT_URL, params)
        print(green(f'Job updated {jobId}'), flush=True)
