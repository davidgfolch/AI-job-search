import math
from commonlib.terminalColor import green, yellow
from commonlib.environmentUtil import getEnv
from ..core import baseScrapper
from ..core.utils import debug
from ..core.baseScrapper import getAndCheckEnvVars
from ..navigator.glassdoorNavigator import GlassdoorNavigator
from ..services.GlassdoorService import GlassdoorService
from ..services.selenium.browser_service import sleep
from .BaseExecutor import BaseExecutor

class GlassdoorExecutor(BaseExecutor):
    def _init_scrapper(self):
        self.site_name = "GLASSDOOR"
        self.jobs_x_page = 30
        self.user_email, self.user_pwd, self.jobs_search = getAndCheckEnvVars(self.site_name)
        self.jobs_search_base_url = getEnv(f'{self.site_name}_JOBS_SEARCH_BASE_URL')
        self.navigator = GlassdoorNavigator(self.selenium_service, self.debug)

    def _preload_action(self):
        self.navigator.load_main_page()
        self.navigator.login(self.user_email, self.user_pwd)

    def _create_service(self, mysql):
        return GlassdoorService(mysql, self.persistence_manager, self.debug)

    def _process_keyword(self, keyword: str, start_page: int):
        url = self.jobs_search_base_url.format(**{'search': keyword})
        print(f'Search keyword={keyword}')
        self.navigator.load_page(url)
        sleep(2,2)
        totalResults = self.navigator.get_total_results(keyword)
        if totalResults < 1:
            print(yellow(f'No results found for keyword={keyword}'))
            return 
        self.navigator.close_dialogs()
        totalPages = math.ceil(totalResults / self.jobs_x_page)
        page = self.navigator.fast_forward_page(start_page, totalResults, self.jobs_x_page)
        currentItem = (page - 1) * self.jobs_x_page
        while currentItem < totalResults:
            baseScrapper.printPage('Glassdoor', page, totalPages, keyword)
            idx = 0
            while idx < self.jobs_x_page and currentItem < totalResults:
                print(green(f'pg {page} job {idx + 1} - '), end='', flush=True)
                self._load_and_process_row(idx)
                currentItem += 1
                idx += 1
            if currentItem < totalResults:
                if self.navigator.click_next_page():
                    page += 1
                    self.navigator.wait_until_page_is_loaded()
                    self.service.update_state(keyword, page)
                else:
                    break
        baseScrapper.summarize(keyword, totalResults, currentItem)

    def _load_and_process_row(self, idx):
        try:
            all_lis = self.navigator.get_job_li_elements()
            if idx >= len(all_lis):
                 return
            
            # Scroll logic from original
            self.navigator.scroll_jobs_list(idx)
            # Re-fetch after scroll as per original logic (though sometimes dangerous if DOM changes, but copying original logic)
            all_lis = self.navigator.get_job_li_elements()
            if idx >= len(all_lis): # Safety check again
                 return
            li_elm = all_lis[idx]
            
            url = self.navigator.get_job_url(li_elm)
            job_id, job_exists = self.service.job_exists_in_db(url)
            
            if job_exists:
                print(yellow(f'Job id={job_id} already exists in DB, IGNORED.'), end='')
            else:
                self.navigator.load_job_detail(li_elm)
                sleep(1,1)
                try:
                    title, company, location, url, html = self.navigator.get_job_data()
                    easy_apply = self.navigator.check_easy_apply()
                    self.service.process_job(title, company, location, url, html, easy_apply)
                finally:
                    self.navigator.go_back()
        except Exception:
            debug(self.debug, exception=True)
        finally:
            print(flush=True)
