import math
from selenium.common.exceptions import NoSuchElementException
from commonlib.terminalColor import yellow, green
from commonlib.decorator.retry import retry
from ..core import baseScrapper
from ..core.utils import debug
from ..core.baseScrapper import getAndCheckEnvVars
from ..services.selenium.browser_service import sleep
from ..navigator.linkedinNavigator import LinkedinNavigator
from ..services.LinkedinService import LinkedinService
from .BaseExecutor import BaseExecutor

class LinkedinExecutor(BaseExecutor):
    def _init_scrapper(self):
        self.site_name = "LINKEDIN"
        self.jobs_x_page = 25
        self.remote = '2'   # onsite "1", remote "2", hybrid "3"
        self.location = '105646813' # Spain
        self.f_TPR = 'r86400'  # last 24 hours
        self.user_email, self.user_pwd, self.jobs_search = getAndCheckEnvVars(self.site_name)
        self.navigator = LinkedinNavigator(self.selenium_service)
        self.debug = False

    def _preload_action(self):
        self.navigator.login(self.user_email, self.user_pwd)
        print(yellow('Waiting for LinkedIn to redirect to feed page... (Maybe you need to solve a security filter first)'))
        self.navigator.wait_until_page_url_contains('https://www.linkedin.com/feed/', 60)

    def _create_service(self, mysql):
        return LinkedinService(mysql, self.persistence_manager)

    def _process_keyword(self, keyword: str, start_page: int):
        url = self._load_page(keyword)
        if self.navigator.check_login_popup(lambda: self.navigator.login(self.user_email, self.user_pwd)):
            url = self._load_page(keyword)
        
        if self.navigator.check_results(keyword, url, self.remote, self.location, self.f_TPR):
            self._search_jobs_loop(keyword, start_page)

    def _load_page(self, keywords: str) -> str:
        from urllib.parse import quote
        print(f'Search keyword={keywords}')
        url = f'https://www.linkedin.com/jobs/search/?keywords={quote(keywords)}&f_WT={self.remote}&geoId={self.location}&f_TPR={self.f_TPR}'
        self.navigator.load_page(url)
        return url

    def _search_jobs_loop(self, keywords: str, startPage: int):
        try:
            self.navigator.collapse_messages()
            totalResults = self.navigator.get_total_results(keywords, self.remote, self.location, self.f_TPR)
            totalPages = math.ceil(totalResults / self.jobs_x_page)
            page = self.navigator.fast_forward_page(startPage, totalResults, self.jobs_x_page)
            currentItem = (page - 1) * self.jobs_x_page
            
            while True:
                foundNewJobInPage = False
                baseScrapper.printPage(self.site_name, page, totalPages, keywords)
                rowErrors = 0
                for idx in range(1, self.jobs_x_page + 1):
                    if currentItem >= totalResults:
                        break
                    currentItem += 1
                    print(green(f'pg {page} job {idx} - '), end='', flush=True)
                    result = self._load_and_process_row(idx)
                    if result == "ERROR":
                        rowErrors += 1
                    
                    if rowErrors > 1:
                        break
                    
                    if result is False: 
                        foundNewJobInPage = True

                if currentItem >= totalResults or page >= totalPages:
                    break
                
                if not foundNewJobInPage and (page > startPage + 1 or (startPage < 2 and page > 2)):
                    print(yellow('No new jobs found in this page, stopping keyword processing.'))
                    break
                
                if not self.navigator.click_next_page():
                    break
                
                page += 1
                self.navigator.wait_until_page_is_loaded()
                self.service.update_state(keywords, page)
            
            baseScrapper.summarize(keywords, totalResults, currentItem)
        except Exception:
            debug(self.debug, exception=True)
            
    def _load_and_process_row(self, idx, rowErrors=0) -> bool | str:
        # Returns True (exists), False (new), or "ERROR"
        try:
            cssSel = self.navigator.scroll_jobs_list(idx)
            url = self.navigator.get_job_url_from_element(cssSel)
            jobId, jobExists = self.service.job_exists_in_db(url)
            self.navigator.load_job_detail(jobExists, idx, cssSel)
            if jobExists:
                print(yellow(f'Job id={jobId} already exists in DB, IGNORED.'))
                return True
            self._process_row(idx)
            print()
            return False
        except NoSuchElementException:
            debug(self.debug, "NoSuchElement in loadAndProcessRow ", exception=True)
            print()
            return "ERROR"
        except Exception: # Generic exception handling missing in original specific block, but it had generic catch.
             # Original catch: except NoSuchElementException ...
             # But it didn't catch other things? `search_jobs` catches generic Exception.
             # I will keep `expected NoSuchElementException` behavior.
             debug(self.debug, "Exception in loadAndProcessRow ", exception=True)
             return "ERROR"

    @retry()
    def _process_row(self, idx):
        sleep(2,2)
        isDirectUrlScrapping = idx is None
        try:
            title, company, location, url, html = self.navigator.get_job_data()
            easyApply = self.navigator.check_easy_apply()
            self.service.process_job(title, company, location, url, html, isDirectUrlScrapping, easyApply)
        except (ValueError, KeyboardInterrupt) as e:
            raise e
        except Exception:
            debug(self.debug, exception=True)
            raise

    @classmethod
    def process_specific_url(cls, url: str):
        # Helper logic to transform standard job url to search url
        url = cls._transform_to_search_url(url)
        from commonlib.mysqlUtil import MysqlUtil
        from ..services.selenium.seleniumService import SeleniumService
        from ..util.persistence_manager import PersistenceManager
        
        with MysqlUtil() as mysql, SeleniumService() as seleniumUtil:
             # We need to instantiate ourselves potentially, or just use components directly?
             # Since this replaces `processUrl` logic which used navigator/service directly, 
             # we can do the same or instantiate Executor.
             # Instantiating Executor requires env vars which might not be set in this context?
             # `processUrl` used `USER_EMAIL` global.
             # So we can instantiate Executor.
             pm = PersistenceManager()
             executor = cls(seleniumUtil, pm)
             executor.navigator.load_page(url)
             if executor.navigator.check_login_popup(lambda: executor.navigator.login(executor.user_email, executor.user_pwd)):
                 executor.navigator.load_page(url)
             executor._process_row(None)

    @staticmethod
    def _transform_to_search_url(url: str) -> str:
        import re
        match = re.search(r'linkedin.com/jobs/view/(\d+)', url)
        if match:
            jobId = match.group(1)
            url = f'https://www.linkedin.com/jobs/search/?currentJobId={jobId}'
        return url

