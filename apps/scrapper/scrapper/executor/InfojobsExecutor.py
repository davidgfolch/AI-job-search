import math
from commonlib.terminalColor import green, yellow
from ..core import baseScrapper
from ..core.utils import debug
from ..core.baseScrapper import getAndCheckEnvVars
from ..navigator.infojobsNavigator import InfojobsNavigator
from ..services.InfojobsService import InfojobsService
from .BaseExecutor import BaseExecutor

class InfojobsExecutor(BaseExecutor):
    def _init_scrapper(self):
        self.site_name = "INFOJOBS"
        self.jobs_x_page = 22
        self.list_url = 'https://www.infojobs.net/ofertas-trabajo'
        self.user_email, self.user_pwd, self.jobs_search = getAndCheckEnvVars(self.site_name)
        self.navigator = InfojobsNavigator(self.selenium_service)
        self.debug = True

    def _preload_action(self):
        # For preloading, we can just use the navigator logic
        self.navigator.load_search_page()
        if not self.selenium_service.driverUtil.useUndetected:
            self.navigator.security_filter()

    def _create_service(self, mysql):
        return InfojobsService(mysql, self.persistence_manager)

    def _process_keyword(self, keyword: str, start_page: int):
        print(yellow(f'Search keyword={keyword}'))
        self.navigator.load_search_page()
        if not self.navigator.load_filtered_search_results(keyword):
            return
        totalResults = self.navigator.get_total_results(keyword)
        totalPages = math.ceil(totalResults / self.jobs_x_page)
        page = self.navigator.fast_forward_page(start_page, totalResults, self.jobs_x_page)
        currentItem = (page - 1) * self.jobs_x_page
        
        while currentItem < totalResults:
            foundNewJobInPage = False
            baseScrapper.printPage(self.site_name, page, totalPages, keyword)
            idx = 0
            while idx < self.jobs_x_page and currentItem < totalResults:
                print(green(f'pg {page} job {idx+1} - '), end='', flush=True)
                jobExistsInDb = self._load_and_process_row(idx)
                if not jobExistsInDb:
                    foundNewJobInPage = True
                currentItem += 1
                idx += 1
            
            if not foundNewJobInPage and (page > start_page + 1 or (start_page < 2 and page > 2)):
                print(yellow('No new jobs found in this page, stopping keyword processing.'))
                break
            
            if currentItem < totalResults:
                if self.navigator.click_next_page():
                    page += 1
                    self.navigator.wait_until_page_is_loaded()
                    self.service.update_state(keyword, page)
                else:
                    break
        
        baseScrapper.summarize(keyword, totalResults, currentItem)

    def _load_and_process_row(self, idx) -> bool:
        try:
            if idx > 2:
                try:
                    self.navigator.scroll_jobs_list(idx)
                except Exception:
                    print(yellow(f'Could not scroll to link {idx+1}, IGNORING.'), end='')
                    return False
            job_link_elm = self.navigator.get_job_link_element(idx)
            url = self.navigator.get_job_url(job_link_elm)
            job_id, job_exists = self.service.job_exists_in_db(url)
            if job_exists:
                print(yellow(f'Job id={job_id} already exists in DB, IGNORED.'), end='', flush=True)
                return True
            print(yellow('loading...'), end='')

            self.navigator.click_job_link(job_link_elm)
            if not self._process_row(url):
                 raise ValueError('Validation failed')
        except Exception:
            debug(self.debug, exception=True)
            return False
        finally:
            print(flush=True)
            if self.list_url not in self.navigator.get_url():
                self.navigator.go_back()
        return False

    def _process_row(self, url):
        try:
            title, company, location, _, html = self.navigator.get_job_data()
            return self.service.process_job(title, company, location, url, html)
        except Exception as e:
            debug(self.debug, exception=True)
            raise e
