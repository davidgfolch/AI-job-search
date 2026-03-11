import math
from commonlib.terminalColor import green, yellow, red
from commonlib.decorator.retry import retry
from ..core import baseScrapper
from ..core.utils import debug
from ..core.baseScrapper import getAndCheckEnvVars
from commonlib.environmentUtil import getEnv
from ..navigator.indeedScraplingNavigator import IndeedScraplingNavigator
from ..services.IndeedService import IndeedService
from .BaseExecutor import BaseExecutor

class IndeedScraplingExecutor(BaseExecutor):
    """Execution logic for Indeed using Scrapling framework to bypass Cloudflare"""

    def _init_scrapper(self):
        self.site_name = "INDEED"
        self.jobs_x_page = 16 
        self.location = "España"
        self.remote = True
        self.days_old = 3
        self.user_email, self.user_pwd, self.jobs_search = getAndCheckEnvVars(self.site_name)
        proxies_str = getEnv('SCRAPPER_INDEED_PROXIES')
        proxies_list = [p.strip() for p in proxies_str.split(',')] if proxies_str and proxies_str.strip() else None
        print(f"Using scrapling implementation (proxies={proxies_list})")
        self.navigator = IndeedScraplingNavigator(proxies_list, self.debug)

    def _preload_action(self):
        # No login needed for scrapling - it handles Cloudflare automatically
        pass

    def _create_service(self, mysql):
        # We reuse the same DB Service logic as Selenium
        return IndeedService(mysql, self.persistence_manager, self.debug)

    def _checkNoResults(self, keyword):
        if self.navigator.checkNoResults():
            print(yellow(f"No results for search={keyword}"))
            return False
        return True

    def _execute_scrapping(self):
        try:
            super()._execute_scrapping()
        finally:
            self.navigator.close()

    def _process_keyword(self, keyword: str, start_page: int):
        import time, random
        time.sleep(random.uniform(5, 10))
        print(f"Search keyword={keyword} using Scrapling")
        
        # Ensure our session gets this search running
        self.navigator.search(keyword, self.location, self.remote, self.days_old, start_page)
        
        if not self._checkNoResults(keyword):
            return
            
        self.navigator.clickSortByDate()
        time.sleep(3)
            
        totalResults = self.navigator.get_total_results(keyword)
        job_links = self.navigator.get_page_job_links()
        
        if totalResults == 0:
            if not job_links:
                print(yellow(f"No results found for {keyword}"))
                return
            else:
                print(yellow(f"Total results count not found, but {len(job_links)} links discovered. Proceeding..."))
                totalResults = len(job_links) # fallback estimate
            
        page = self.navigator.fast_forward_page(start_page, totalResults, self.jobs_x_page) - 1
        totalPages = math.ceil(totalResults/self.jobs_x_page) if totalResults > 0 else 1
        currentItem = max(0, page * self.jobs_x_page)
        while True:
            page += 1
            baseScrapper.printPage('Indeed', page, totalPages, keyword)
            idx = 0
            foundNewJobInPage = False
            job_links = self.navigator.get_page_job_links()
            while idx < min(len(job_links), self.jobs_x_page):
                print(green(f"pg {page} job {idx + 1} - "), end="")
                if self._load_and_process_row(job_links[idx]):
                    foundNewJobInPage = True
                currentItem += 1
                print()
                idx += 1
            if not foundNewJobInPage and (page > start_page + 1 or (start_page < 2 and page > 2)):
                print(yellow("No new jobs found in this page, stopping keyword processing."))
                break
            if self.navigator.click_next_page():
                self.service.update_state(keyword, page + 1)
            else:
                break    
        baseScrapper.summarize(keyword, totalResults, currentItem)

    def _load_and_process_row(self, initial_url) -> bool:
        """Return true if job was inserted"""
        ignore = True
        try:
            jobId, jobExists = self.service.job_exists_in_db(initial_url)
            if jobExists:
                print(yellow(f"Job id={jobId} already exists in DB, IGNORED."), end="", flush=True)
                return False
            self.navigator.load_job_detail(initial_url)
            url = self.navigator.get_current_job_url()
            ignore = False
        except Exception:
            debug(self.debug)
            
        if not ignore:
            if not self._process_row(url):
                print(red("Validation failed"))
                return False
            return True
        return False

    @retry(raiseException=False)
    def _process_row(self, url):
        title, company, location, _, html = self.navigator.get_job_data()
        easyApply = self.navigator.check_easy_apply()
        return self.service.process_job(title, company, location, url, html, easyApply)
