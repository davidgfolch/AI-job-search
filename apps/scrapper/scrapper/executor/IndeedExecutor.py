import math
from commonlib.terminalColor import green, yellow, red
from commonlib.decorator.retry import retry
from ..core import baseScrapper
from ..core.utils import debug
from ..core.baseScrapper import getAndCheckEnvVars
from ..services.selenium.browser_service import sleep
from ..navigator.indeedNavigator import IndeedNavigator
from ..services.IndeedService import IndeedService
from .BaseExecutor import BaseExecutor

class IndeedExecutor(BaseExecutor):

    def _init_scrapper(self):
        self.site_name = "INDEED"
        self.jobs_x_page = 15 # Indeed usually 15 or 16
        # Original indeed.py said 16 but commented "usually 1 row is hidden". I'll use 16 as in original.
        self.jobs_x_page = 16 
        self.location = "España"
        self.remote = True
        self.days_old = 3
        self.user_email, self.user_pwd, self.jobs_search = getAndCheckEnvVars(self.site_name)
        self.navigator = IndeedNavigator(self.selenium_service, self.debug)

    def _preload_action(self):
        self.navigator.login()

    def _create_service(self, mysql):
        return IndeedService(mysql, self.persistence_manager, self.debug)

    def _checkNoResults(self, keyword):
        self.navigator.wait_until_page_is_loaded()
        sleep(2,2)
        if self.navigator.checkNoResults():
            print(yellow(f"No results for search={keyword}"))
            return False
        return True

    def _process_keyword(self, keyword: str, start_page: int):
        sleep(3,4)
        print(f"Search keyword={keyword}")
        self.navigator.search(keyword, self.location, self.remote, self.days_old, start_page)
        if not self._checkNoResults(keyword):
            return
        self.navigator.selectFilters(self.remote, self.days_old)
        if not self._checkNoResults(keyword):
            return
        self.navigator.clickSortByDate()
        sleep(3,4)
        self.navigator.wait_until_page_is_loaded()
        totalResults = self.navigator.get_total_results(keyword)
        page = self.navigator.fast_forward_page(start_page, totalResults, self.jobs_x_page) - 1
        totalPages = math.ceil(totalResults/self.jobs_x_page)
        currentItem = (page - 1) * self.jobs_x_page
        while True:
            page += 1
            baseScrapper.printPage('Indeed', page, totalPages, keyword)
            idx = 0
            foundNewJobInPage = False
            while idx < self.jobs_x_page:
                print(green(f"pg {page} job {idx + 1} - "), end="")
                if self._load_and_process_row(idx):
                    foundNewJobInPage = True
                currentItem += 1
                print()
                idx += 1
            if not foundNewJobInPage and (page > start_page + 1 or (start_page < 2 and page > 2)):
                print(yellow("No new jobs found in this page, stopping keyword processing."))
                break
            if self.navigator.click_next_page():
                self.navigator.wait_until_page_is_loaded()
                sleep(5, 6)
                self.service.update_state(keyword, page + 1)
            else:
                break
        baseScrapper.summarize(keyword, totalResults, currentItem)

    def _load_and_process_row(self, idx) -> bool:
        """Return true if job was inserted"""
        ignore = True
        jobExists = False
        url = ""
        try:
            self.navigator.close_modal()
            if not self.navigator.scroll_jobs_list(idx):
                return False
            sleep(0.5, 1)
            jobLinkElm = self.navigator.get_job_link_element(idx)
            initial_url = self.navigator.get_job_url(jobLinkElm)
            jobId, jobExists = self.service.job_exists_in_db(initial_url)
            if jobExists:
                print(yellow(f"Job id={jobId} already exists in DB, IGNORED."), end="", flush=True)
                return False
            self.navigator.load_job_detail(jobLinkElm)
            sleep(2, 2)
            url = self.navigator.selenium.getUrl()
            ignore = False
        except IndexError as ex:
            print(yellow(f"WARNING: could not get all items per page, that's expected because not always has {self.jobs_x_page} pages: {ex}"), end='')
        except Exception:
            debug(self.debug)
        if not ignore:
            if not self._process_row(url):
                print(red("Validation failed"))
                return self._load_and_process_row(idx)
            sleep(1, 2)
            return True
        return False

    @retry(raiseException=False)
    def _process_row(self, url):
        title, company, location, _, html = self.navigator.get_job_data()
        easyApply = self.navigator.check_easy_apply()
        return self.service.process_job(title, company, location, url, html, easyApply)
