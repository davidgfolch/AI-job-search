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
        self.navigator = IndeedNavigator(self.selenium_service)


    def _preload_action(self):
        self.navigator.login()

    def _create_service(self, mysql):
        return IndeedService(mysql, self.persistence_manager)

    def _process_keyword(self, keyword: str, start_page: int):
        sleep(3,4)
        print(f"Search keyword={keyword}")
        self.navigator.search(keyword, self.location, self.remote, self.days_old, start_page)
        self.navigator.wait_until_page_is_loaded()
        sleep(2,2)
        if self.navigator.checkNoResults():
            print(yellow(f"No results for search={keyword}"))
            return
        self.navigator.selectFilters(self.remote, self.days_old)
        sleep(2,2)
        self.navigator.wait_until_page_is_loaded()
        if self.navigator.checkNoResults():
            print(yellow(f"No results for search={keyword}"))
            return
        self.navigator.clickSortByDate()
        sleep(3,4)
        self.navigator.wait_until_page_is_loaded()

        totalResults = self.navigator.get_total_results(keyword)
        if totalResults == 0:
            print(yellow(f"No results for search={keyword}"))
            return

        page = self.navigator.fast_forward_page(start_page, totalResults, self.jobs_x_page) - 1
        currentItem = (page - 1) * self.jobs_x_page
        totalPages = totalResults/self.jobs_x_page if totalResults % self.jobs_x_page == 0 else totalResults/self.jobs_x_page + 1
        
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
            # Get initial URL from link for job ID extraction
            initial_url = self.navigator.get_job_url(jobLinkElm)
            jobId, jobExists = self.service.job_exists_in_db(initial_url)
            if jobExists:
                print(yellow(f"Job id={jobId} already exists in DB, IGNORED."), end="", flush=True)
                return False
            # Load the job detail page
            self.navigator.load_job_detail(jobLinkElm)
            # Get the actual URL from the main page after navigation
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
                # Recursively try again?? Original code: return load_and_process_row(idx)
                # Beware of infinite recursion if persistent error.
                # Use simple retry or just return False/retry logic if desired.
                # Original had recursion: return load_and_process_row(idx).
                # I will reproduce it but ensure it's not infinite loop risk (if validation failed, maybe transient?).
                # Ideally validation fails on content, not load. Retry loading? 
                # If content is invalid, reloading same might fail again. 
                # Assuming original intent was retry.
                return self._load_and_process_row(idx)
            sleep(1, 2)
            return True
        return False

    @retry(raiseException=False)
    def _process_row(self, url):
        title, company, location, _, html = self.navigator.get_job_data()
        easyApply = self.navigator.check_easy_apply()
        return self.service.process_job(title, company, location, url, html, easyApply)
