import math
from urllib.parse import quote
from commonlib.terminalColor import green, yellow
from ..core import baseScrapper
from ..core.utils import debug
from ..core.baseScrapper import getAndCheckEnvVars, join, printPage
from ..navigator.tecnoempleoNavigator import TecnoempleoNavigator
from ..services.TecnoempleoService import TecnoempleoService
from .BaseExecutor import BaseExecutor

class TecnoempleoExecutor(BaseExecutor):
    def _init_scrapper(self):
        self.site_name = "TECNOEMPLEO"
        self.jobs_x_page = 30
        self.remote = ',1,'
        self.user_email, self.user_pwd, self.jobs_search = getAndCheckEnvVars(self.site_name)
        self.navigator = TecnoempleoNavigator(self.selenium_service)
        self.debug = False

    def _preload_action(self):
        self.navigator.load_page('https://www.tecnoempleo.com')
        self.navigator.login(self.user_email, self.user_pwd)
        print(yellow('Waiting for Tecnoempleo to redirect to jobs page...'))
        self.navigator.selenium.waitUntilPageUrlContains('https://www.tecnoempleo.com/profesionales/candidat.php', 60)

    def _create_service(self, mysql):
        return TecnoempleoService(mysql, self.persistence_manager)

    def _process_keyword(self, keyword: str, start_page: int):
        try:
            print(yellow(f'Search keyword={keyword}'))
            url = self._get_url(keyword)
            print(yellow(f'Loading page {url}'))
            self.navigator.load_page(url)
            if not self.navigator.check_results(keyword, url, self.remote):
                return
            self.navigator.accept_cookies()
            totalResults = self.navigator.get_total_results(keyword, self.remote)
            totalPages = math.ceil(totalResults / self.jobs_x_page)
            page = self.navigator.fast_forward_page(start_page, totalResults, self.jobs_x_page)
            currentItem = (page - 1) * self.jobs_x_page
            
            while True:  # Pagination
                errors = 0
                printPage(self.site_name, page, totalPages, keyword)
                foundNewJobInPage = False
                
                for idx in range(1, self.jobs_x_page + 1):
                    if currentItem >= totalResults:
                        break
                    currentItem += 1
                    print(green(f'pg {page} job {idx} - '), end='')
                    liIdx = 3 + (idx - 1) * 2  # li starts at 3 & step 2
                    ok, jobExistsInDb = self._load_and_process_row(liIdx, errors)
                    
                    if not ok:
                        if self.navigator.check_rate_limit():
                            return # Original returned False/void
                        
                        # Update errors
                         # logic inside _load_and_process_row incremented errors count which was local? 
                         # Same issue as Linkedin.
                         # I will fix logic here:
                        errors += 1
                        if errors > 1:
                            break
                    else: 
                         # Reset errors if success? Original didn't.
                         pass

                    if ok and not jobExistsInDb:
                        foundNewJobInPage = True

                if currentItem >= totalResults:
                    break
                
                if not foundNewJobInPage and (page > start_page + 1 or (start_page < 2 and page > 2)):
                    print(yellow('No new jobs found in this page, stopping keyword processing.'))
                    break
                
                if not self.navigator.click_next_page():
                    break
                
                page += 1
                self.navigator.wait_until_page_is_loaded()
                self.service.update_state(keyword, page)
                
            baseScrapper.summarize(keyword, totalResults, currentItem)
        except Exception:
            debug(self.debug, exception=True)

    def _get_url(self, keywords):
        return join('https://www.tecnoempleo.com/ofertas-trabajo/?',
                    '&'.join([
                        f'te={quote(keywords)}',
                        f'en_remoto={self.remote}',
                    ]))

    def _load_and_process_row(self, idx, errors_count): # errors_count unused inside but passed for legacy?
        """
        Returns ok: bool, jobExistsInDb: bool
        """
        pageLoaded = False
        try:
            cssSelLink = self.navigator.scroll_jobs_list(idx)
            url = self.navigator.get_attribute(cssSelLink, 'href')
            job_id, job_exists = self.service.job_exists_in_db(url)
            if job_exists:
                print(yellow(f'Job id={job_id} already exists in DB, IGNORED.'), end='')
                return True, True
            print(yellow('loading...'), end='')
            pageLoaded = self.navigator.load_detail(cssSelLink)
            self._process_row()
            return True, False
        except Exception:
            debug(self.debug, exception=True)
            return False, False
        finally:
            print(flush=True)
            if pageLoaded:
                self.navigator.go_back()

    def _process_row(self):
        title, company, location, url, html = self.navigator.get_job_data()
        return self.service.process_job(title, company, location, url, html)
