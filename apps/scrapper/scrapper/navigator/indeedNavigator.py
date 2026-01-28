from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from commonlib.decorator.retry import retry, StackTrace
from commonlib.terminalColor import green, yellow, printHR
from commonlib.stringUtil import join
from ..core import baseScrapper
from ..services.selenium.seleniumService import SeleniumService
from ..services.selenium.browser_service import sleep
from ..services.gmail.indeed_gmail_service import IndeedGmailService
import re

# Get Indeed credentials from environment
USER_EMAIL, USER_PWD, _ = baseScrapper.getAndCheckEnvVars("INDEED")
from ..selectors.indeedSelectors import *
from .baseNavigator import BaseNavigator

class IndeedNavigator(BaseNavigator):
    def accept_cookies(self):
        self.selenium.waitAndClick_noError(CSS_SEL_COOKIE_ACCEPT, "Could not accept cookies")

    @retry(retries=60, delay=1, raiseException=False, stackTrace=StackTrace.NEVER)
    def waitForCloudflareFilterInLogin(self):
        self.selenium.waitUntil_presenceLocatedElement(CSS_SEL_LOGIN_EMAIL)
        return True

    def login(self):
        print("Navigating to Indeed login page...")
        self.selenium.loadPage(LOGIN_PAGE)
        self.selenium.waitUntilPageIsLoaded()
        sleep(1,1)
        if self.selenium.waitUntil_presenceLocatedElement_noError('#AccountMenu'):
            return
        if not self.waitForCloudflareFilterInLogin():
            raise Exception("Could not login because cloudFlare security filter was not resolved")
        print("Filling login form...")
        self.selenium.sendKeys(CSS_SEL_LOGIN_EMAIL, USER_EMAIL)
        self.accept_cookies()
        print("Submitting login form...")
        self.selenium.waitAndClick(CSS_SEL_LOGIN_SUBMIT)
        print("Waiting for Cloudflare filter...")
        sleep(5, 5)
        if not self.selenium.waitAndClick_noError(CSS_SEL_LOGIN_SUBMIT,
            "Could not resubmit login form after cloudflare filter...",
            showException=False):
            sleep(3, 3)
        print("Handling Google OTP fallback...")
        self.click_google_otp_fallback()
        print("Get email 2FA code...")
        self.getEmail2faCode()
        print("Ignore Access key form question")
        sleep(2, 3)
        self.ignore_access_key_form()
        sleep(2, 3)

    def search(self, keyword: str, location: str, remote: bool, daysOld: int, startPage: int):
        print(f'Searching for "{keyword}" in "{location}"')
        self.selenium.waitUntil_presenceLocatedElement(CSS_SEL_SEARCH_WHAT)
        self.selenium.setFocus(CSS_SEL_SEARCH_WHAT)
        self.selenium.waitAndClick_noError('button[aria-label="Clear what input"]', "Could not clear keyword input", showException=False)
        self.selenium.setFocus(CSS_SEL_SEARCH_WHERE)
        self.selenium.waitAndClick_noError('button[aria-label="Clear location input"]', "Could not clear location input", showException=False)
        sleep(1,1)
        self.selenium.sendKeys(CSS_SEL_SEARCH_WHAT, keyword, clear=True)
        self.selenium.sendKeys(CSS_SEL_SEARCH_WHERE, location, clear=True)
        self.selenium.waitAndClick(CSS_SEL_SEARCH_BTN)
        self.selenium.waitUntilPageIsLoaded()

    def checkNoResults(self):
        self.close_modal()
        return len(self.selenium.getElms(".jobsearch-NoResult-messageContainer")) > 0

    @retry()
    def selectFilters(self, remote: bool, daysOld: int):
        if remote:
            if not len(self.selenium.getElms("#remote_option_remote")) > 0: # already selected
                self.selectOption("#remote_filter_button", "a[role='menuitem'][aria-label='Teletrabajo']")
        if not len(self.selenium.getElms("#fromAge_option_fromAge")) > 0: # already selected
            self.selectOption(f"#fromAge_filter_button", f"a[role='menuitem'][aria-label*='{daysOld}'][aria-label*='días']")

    @retry(exception=ElementClickInterceptedException, exceptionFnc=lambda self, *args, **kwargs: self.close_modal())
    def selectOption(self, cssSel: str, cssSelOption: str):
        self.selenium.waitAndClick(cssSel)
        sleep(1,1)
        self.selenium.waitAndClick(cssSelOption)
        sleep(3,3)

    def clickSortByDate(self):
        self.selenium.waitAndClick(CSS_SEL_SORT_BY_DATE)

    def get_total_results(self, keywords: str) -> int:
        total = self.selenium.getText(CSS_SEL_JOB_COUNT)
        total = re.findall(r'[0-9.,]+', total)[0]
        printHR()
        print(green(join(f"{total} total results for search: {keywords}")))
        printHR()
        return int(total.replace(".", "").replace(",", ""))

    def scroll_to_bottom(self):
        """ pre scroll to bottom to force load of li's """
        print("scrollToBottom... ", end='')
        self.selenium.scrollProgressive(600)
        self.selenium.scrollProgressive(-1200)
        sleep(1, 2)

    @retry(exception=ElementNotInteractableException, exceptionFnc=lambda self, *args, **kwargs: self.close_modal())
    def scroll_jobs_list(self, idx):
        li = self.selenium.getElms(CSS_SEL_JOB_LI)[idx]
        if not li.is_displayed(): # ignore hidden li's
            return False
        self.selenium.scrollIntoView(li)
        return True

    @retry(retries=3, delay=1, raiseException=False, stackTrace=StackTrace.NEVER)
    def click_next_page(self):
        sleep(1, 2)
        self.close_modal()
        self.selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON)
        return True

    def close_modal(self):
        """ Close modal 'email me with new offers'.  It appears randomly in time after search """
        modals = self.selenium.getElms(CSS_SEL_JOB_MODAL_CLOSE_BTN)
        if modals:
            self.selenium.waitAndClick(modals[0])

    @retry(exception=ElementClickInterceptedException, exceptionFnc=lambda self, *args, **kwargs: self.close_modal())
    def load_job_detail(self, jobLinkElm: WebElement):
        print(yellow("loading..."), end="")
        self.selenium.waitAndClick(jobLinkElm)

    def get_job_link_element(self, idx):
        liElm = self.selenium.getElms(CSS_SEL_JOB_LI)[idx]
        return self.selenium.getElmOf(liElm, CSS_SEL_JOB_LINK)

    def get_job_url(self, element: WebElement) -> str:
        url = element.get_attribute("href")
        return baseScrapper.removeUrlParameter(url, 'cf-turnstile-response')


    def get_job_data(self):
        title = self.selenium.getText(CSS_SEL_JOB_TITLE).removesuffix("\n- job post")
        company = self.selenium.getText(CSS_SEL_COMPANY)
        location = self.selenium.getText(CSS_SEL_LOCATION)
        html = self.selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
        url = self.selenium.getUrl()
        return title, company, location, url, html

    def check_easy_apply(self):
        return len(self.selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0

    def click_google_otp_fallback(self):
        self.selenium.waitAndClick(CSS_SEL_GOOGLE_OTP_FALLBACK)
        sleep(5, 5)

    @retry(delay=1)
    def getEmail2faCode(self):
        sleep(5, 5)
        with IndeedGmailService() as gmail:
            code = gmail.wait_for_verification_code("login@indeed.com", 60)
        self.selenium.sendKeys(CSS_SEL_2FA_PASSCODE_INPUT, code)
        self.selenium.waitAndClick(CSS_SEL_2FA_VERIFY_SUBMIT)
        self.selenium.waitUntilPageIsLoaded()
        inputError = self.selenium.getElms("#label-passcode-input-error")
        if len(inputError) > 0 and inputError[0].is_displayed(): # invalid code, try again
            raise ValueError("Invalid code")

    def ignore_access_key_form(self):
        self.selenium.waitUntil_presenceLocatedElement(CSS_SEL_WEBAUTHN_CONTINUE)
        self.selenium.waitAndClick(CSS_SEL_WEBAUTHN_CONTINUE)
        self.selenium.waitUntilPageIsLoaded()


