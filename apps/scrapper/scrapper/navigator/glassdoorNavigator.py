from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from commonlib.decorator.retry import retry
from commonlib.terminalColor import yellow, green, printHR
from ..services.selenium.seleniumService import SeleniumService
from ..services.selenium.browser_service import sleep
from ..selectors.glassdoorSelectors import (
    CSS_SEL_COMPANY, CSS_SEL_COMPANY2, CSS_SEL_COOKIES_ACCEPT, CSS_SEL_DIALOG_CLOSE,
    CSS_SEL_INPUT_PASS, CSS_SEL_JOB_DESCRIPTION, CSS_SEL_JOB_EASY_APPLY, CSS_SEL_JOB_LI,
    CSS_SEL_JOB_TITLE, CSS_SEL_LOCATION, CSS_SEL_NEXT_PAGE_BUTTON, CSS_SEL_PASSWORD_SUBMIT,
    CSS_SEL_SEARCH_RESULT_TOTAL, LI_JOB_TITLE_CSS_SUFFIX
)
from .baseNavigator import BaseNavigator

class GlassdoorNavigator(BaseNavigator):

    def load_main_page(self):
        self.selenium.loadPage('https://www.glassdoor.es/index.htm')
        try:
            self.selenium.waitUntil_presenceLocatedElement('#inlineUserEmail')
        except Exception:  # reload page, it get hung sometimes
            self.selenium.loadPage('https://www.glassdoor.es/index.htm')
            try:
                self.selenium.waitUntil_presenceLocatedElement('#inlineUserEmail')
            except Exception:
                if not self.selenium.usesUndetectedDriver():
                    self.security_filter()

    @retry(retries=60, delay=5, exception=NoSuchElementException)
    def security_filter(self):
        print(yellow('SOLVE A SECURITY FILTER in selenium webbrowser...'), end='')
        sleep(4, 4)
        self.selenium.getElm('#inlineUserEmail')

    @retry()
    def login(self, user_email, user_pwd):
        self.load_main_page()
        self.selenium.sendKeys('#inlineUserEmail', user_email)
        sleep(2, 5)
        self.selenium.waitAndClick('.emailButton button[type=submit]')
        sleep(2, 5)
        self.selenium.waitUntilPageIsLoaded()
        sleep(1, 2)
        # 'login password slider wait'
        self.selenium.waitUntilClickable(CSS_SEL_PASSWORD_SUBMIT)
        self.selenium.waitUntil_presenceLocatedElement(CSS_SEL_PASSWORD_SUBMIT)
        self.selenium.waitUntil_presenceLocatedElement(CSS_SEL_INPUT_PASS)
        self.selenium.sendKeys(CSS_SEL_INPUT_PASS, user_pwd)
        sleep(1, 2)
        self.selenium.waitAndClick(CSS_SEL_PASSWORD_SUBMIT)
        print(yellow('Waiting for Glassdoor to redirect after login...'))
        self.selenium.waitUntilPageUrlContains('https://www.glassdoor.es/Job/index.htm', 60)


    @retry()
    def get_total_results(self, keywords: str) -> int:
        total = self.selenium.getText(CSS_SEL_SEARCH_RESULT_TOTAL).split(' ')[0]
        printHR(green)
        print(green(f'{total} total results for search: {keywords}'))
        printHR(green)
        return int(total)

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
        href = self.get_job_url(li_elm)
        self.selenium.loadPage(href)

    def get_job_data(self):
        title = self.selenium.getText(CSS_SEL_JOB_TITLE)
        company_elms = self.selenium.getElms(CSS_SEL_COMPANY)
        if len(company_elms) == 1:
            company = company_elms[0].text
        else:
            company = self.selenium.getText(CSS_SEL_COMPANY2)
        location = self.selenium.getText(CSS_SEL_LOCATION)
        url = self.selenium.getUrl()
        html = self.selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
        return title, company, location, url, html

    def check_easy_apply(self):
        return len(self.selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0



    def wait_until_page_url_contains(self, pattern, timeout):
        self.selenium.waitUntilPageUrlContains(pattern, timeout)
