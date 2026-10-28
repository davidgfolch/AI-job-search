import re
from selenium.common.exceptions import NoSuchElementException
from commonlib.decorator.retry import retry
from commonlib.observability import get_logger
from commonlib.terminalColor import green, yellow, printHR
from ..services.selenium.seleniumService import SeleniumService
from ..services.selenium.browser_service import sleep
from .baseNavigator import BaseNavigator
from .components.glassdoorAuthenticator import GlassdoorAuthenticator

logger = get_logger("scrapper.glassdoorNavigator")

CSS_SEL_SEARCH_RESULT_TOTAL = 'div#left-column h1, h1[data-test="search-title"]'
CSS_SEL_COOKIES_ACCEPT = 'button#onetrust-accept-btn-handler'
CSS_SEL_GLOBAL_ALERT_HIDE = 'CSS_SEL_GLOBAL_ALERT_HIDE'
CSS_SEL_DIALOG_CLOSE = 'dialog[open] button[data-test="auth-modal-close-button"], div[data-test="Modal-content"] button[data-test=job-alert-modal-close]'
CSS_SEL_NO_RESULTS = 'div[class*="notice_NoticeContainer"], div.ErrorPage_errorPage__5lJBV'
CSS_SEL_JOB_LI = 'div#left-column ul li[data-test="jobListing"]'
CSS_SEL_JOB_DETAIL = 'div[class*="JobDetails_jobDetailsContainer"]'
CSS_SEL_COMPANY = f'{CSS_SEL_JOB_DETAIL} [class*="EmployerProfile_compactEmployerName"]'
CSS_SEL_COMPANY2 = f'{CSS_SEL_JOB_DETAIL} [class*="EmployerProfile_employerNameContainer"] h4'
CSS_SEL_LOCATION = f'{CSS_SEL_JOB_DETAIL} header[data-test="job-details-header"] div[data-test="location"]'
LI_JOB_TITLE_CSS_SUFFIX = 'a[data-test="job-title"], a[class*="JobCard_jobTitle__"]'
CSS_SEL_NEXT_PAGE_BUTTON = 'div#left-column button[data-test="load-more"]'
CSS_SEL_JOB_TITLE = f'{CSS_SEL_JOB_DETAIL} h1'
CSS_SEL_JOB_DESCRIPTION = f'{CSS_SEL_JOB_DETAIL} [class*="JobDetails_jobDescription"]'
CSS_SEL_JOB_EASY_APPLY = f'{CSS_SEL_JOB_DETAIL} button[data-test="easyApply"]'
CSS_SEL_JOB_DETAIL_TITLE_ID = '#jd-job-title-{}'
CSS_SEL_AUTH_MODAL_CLOSE = 'dialog[open] button[data-test="auth-modal-close-button"]'


class GlassdoorNavigator(BaseNavigator):

    def __init__(self, selenium: SeleniumService, debug: bool):
        super().__init__(selenium, debug)
        self.authenticator = GlassdoorAuthenticator(selenium)
        self.current_job_url: str | None = None

    @retry(delay=5, exceptionFnc=lambda self, *args, **kwargs: None if self.selenium.usesUndetectedDriver() else self.security_filter())
    def load_main_page(self):
        self.selenium.loadPage('https://www.glassdoor.es/index.htm')
        sleep(2, 2)

    @retry(retries=60, delay=5, exception=NoSuchElementException)
    def security_filter(self):
        print(yellow('SOLVE A SECURITY FILTER in selenium webbrowser...'), end='')
        sleep(4, 4)
        self.selenium.waitUntilPageIsLoaded()

    def login(self):
        logger.info("glassdoor.auth.login_started", method="indeed_otp", console='Logging in via Indeed OTP...')
        self.authenticator.login()

    @retry()
    def get_total_results(self, keywords: str) -> int:
        total = self.selenium.getText(CSS_SEL_SEARCH_RESULT_TOTAL).split(' ')[0]
        printHR(green)
        logger.info("glassdoor.results_found", total=total, keywords=keywords, console=green(f'{total} total results for search: {keywords}'))
        printHR(green)
        return int(total)

    def check_results(self, keywords: str, url: str) -> bool:  # noqa: ARG002 - navigator interface
        noResultElm = self.selenium.getElms(CSS_SEL_NO_RESULTS)
        if len(noResultElm) == 0:
            return True
        printHR(yellow)
        logger.info("glassdoor.no_results", keywords=keywords, console=yellow(f'No results found for keyword={keywords}'))
        printHR(yellow)
        return False

    def close_dialogs(self):
        sleep(1, 2)
        self.selenium.waitAndClick_noError(
            CSS_SEL_DIALOG_CLOSE, 'Could not close dialog', False)
        sleep(1, 2)
        self.selenium.waitAndClick_noError(
            CSS_SEL_COOKIES_ACCEPT,
            'Could not click accept cookies', False)
        sleep(1, 2)

    @retry(exception=NoSuchElementException)
    def click_next_page(self):
        """Click on next to load next page."""
        self.selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON, scrollIntoView=True)
        return True

    def get_job_li_elements(self):
        return self.selenium.getElms(CSS_SEL_JOB_LI)

    def scroll_jobs_list(self, idx):
        if idx < 3:
            return
        li_elms = self.get_job_li_elements()
        if idx < len(li_elms):
            li_elm = li_elms[idx]
            sleep(1, 2)
            self.selenium.scrollIntoView_noError(li_elm)

    def get_job_url(self, li_elm):
        return self.selenium.getAttrOf(li_elm, LI_JOB_TITLE_CSS_SUFFIX, 'href')

    def load_job_detail(self, li_elm):
        print(yellow('loading... '), end='')
        self.current_job_url = self.get_job_url(li_elm)
        self.selenium.waitAndClick(li_elm, scrollIntoView=True)
        if job_id := self._job_id_from_url(self.current_job_url):
            self.selenium.waitUntil_presenceLocatedElement(CSS_SEL_JOB_DETAIL_TITLE_ID.format(job_id))
        sleep(1, 2)
        self.close_auth_modal()

    @staticmethod
    def _job_id_from_url(url: str) -> str | None:
        return match.group(1) if (match := re.search(r'[?&](?:jl|jobListingId)=([0-9]+)', url or '', re.I)) else None

    def close_auth_modal(self):
        """Glassdoor prompts a sign in bottom sheet on some job views, it blocks the next card click until dismissed."""
        if self.selenium.getElms(CSS_SEL_AUTH_MODAL_CLOSE):
            self.selenium.waitAndClick_noError(CSS_SEL_AUTH_MODAL_CLOSE, 'Could not close auth modal', False)

    @retry()
    def get_job_data(self):
        title = self.selenium.getText(CSS_SEL_JOB_TITLE)
        if not (company := self.get_company()):
            raise NoSuchElementException(f'No company found with {CSS_SEL_COMPANY}')
        location = self.selenium.getText(CSS_SEL_LOCATION)
        url = self.current_job_url or self.selenium.getUrl()
        html = self.selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
        return title, company, location, url, html

    def get_company(self) -> str:
        for cssSel in (CSS_SEL_COMPANY, CSS_SEL_COMPANY2):
            for elm in self.selenium.getElms(cssSel):
                if company := (elm.text or '').strip():
                    return company
        return ''

    def check_easy_apply(self):
        return len(self.selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0

    def wait_until_page_url_contains(self, pattern, timeout):
        self.selenium.waitUntilPageUrlContains(pattern, timeout)
