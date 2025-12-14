import re
from typing import Tuple
from commonlib.mysqlUtil import QRY_FIND_JOB_BY_JOB_ID, MysqlUtil
from commonlib.mergeDuplicates import getSelect, mergeDuplicatedJobs
from commonlib.terminalColor import green, magenta, red, yellow
from ...baseScrapper import htmlToMarkdown, validate, debug as baseDebug
from ...persistence_manager import PersistenceManager

class LinkedinJobService:
    def __init__(self, mysql: MysqlUtil, persistence_manager: PersistenceManager):
        self.mysql = mysql
        self.persistence_manager = persistence_manager
        self.web_page = 'Linkedin'
        self.debug = False

    def set_debug(self, debug: bool):
        self.debug = debug

    def get_job_id(self, url: str) -> int:
        return int(re.sub(r'.*/jobs/view/([^/]+)/.*', r'\1', url))

    def get_job_url_short(self, url: str):
        return re.sub(r'(.*/jobs/view/([^/]+)/).*', r'\1', url)

    def job_exists_in_db(self, url: str) -> Tuple[int, bool]:
        jobId = self.get_job_id(url)
        return (jobId, self.mysql.fetchOne(QRY_FIND_JOB_BY_JOB_ID, jobId) is not None)

    def process_job(self, title, company, location, url, html, is_direct_url_scrapping: bool, easy_apply: bool):
        try:
            # Helper logic moved here
            url_short = self.get_job_url_short(url)
            jobId = self.get_job_id(url_short)
            md = htmlToMarkdown(html)
            
            print(f'{jobId}, {title}, {company}, {location}, easy_apply={easy_apply} - ', end='', flush=True)
            
            if validate(title, url_short, company, md, self.debug):
                if is_direct_url_scrapping and self.mysql.jobExists(str(jobId)):
                    self.print_job(title, company, location, url_short, jobId, html, md)
                elif id := self.mysql.insert((jobId, title, company, location, url_short, md, easy_apply, self.web_page)):
                    print(green(f'INSERTED {id}!'), end='', flush=True)
                    mergeDuplicatedJobs(self.mysql, getSelect())
            else:
                raise ValueError('Validation failed')
        except (ValueError, KeyboardInterrupt) as e:
            raise e
        except Exception:
            baseDebug(self.debug, exception=True)

    def print_job(self, title, company, location, url, jobId, html, md):
        print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'))
        print(yellow(f'TITLE={title}'))
        print(yellow(f'COMPANY={company}'))
        print(yellow(f'LOCATION={location}'))
        print(yellow(f'URL={url}'))
        print(yellow(f'HTML:\n', magenta(html)))
        print(yellow(f'MARKDOWN:\n', magenta(md)))

    def prepare_resume(self):
        self.persistence_manager.prepare_resume(self.web_page)

    def should_skip_keyword(self, keyword: str):
        return self.persistence_manager.should_skip_keyword(keyword)

    def update_state(self, keyword: str, page: int):
        self.persistence_manager.update_state(self.web_page, keyword, page)

    def clear_state(self):
        self.persistence_manager.clear_state(self.web_page)
