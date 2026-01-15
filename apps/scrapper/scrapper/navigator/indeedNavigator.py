from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from commonlib.decorator.retry import retry
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


class IndeedNavigator:
    def __init__(self, selenium: SeleniumService):
        self.selenium = selenium

    def accept_cookies(self):
        self.selenium.waitAndClick_noError(CSS_SEL_COOKIE_ACCEPT, "Could not accept cookies")

    def login(self):
        print(yellow("Navigating to Indeed login page..."))
        self.selenium.loadPage(LOGIN_PAGE)
        self.selenium.waitUntilPageIsLoaded()
        sleep(2, 3)
        print(yellow("Filling login form..."))
        self.selenium.sendKeys(CSS_SEL_LOGIN_EMAIL, USER_EMAIL)
        self.accept_cookies()
        print(yellow("Submitting login form..."))
        self.selenium.waitAndClick(CSS_SEL_LOGIN_SUBMIT)
        print(yellow("Waiting for Cloudflare filter..."))
        sleep(5, 5)
        if not self.selenium.waitAndClick_noError(CSS_SEL_LOGIN_SUBMIT,
            "Could not resubmit login form after cloudflare filter...",
            showException=False):
            sleep(3, 3)
        print(yellow("Handling Google OTP fallback..."))
        self.click_google_otp_fallback()
        print(yellow("Get email 2FA code..."))
        self.getEmail2faCode()
        print(yellow("Ignore Access key form question"))
        sleep(2, 3)
        self.ignore_access_key_form()
        sleep(2, 3)

    def search(self, what: str, where: str = "España"):
        print(yellow(f'Searching for "{what}" in "{where}"'))
        self.selenium.waitUntil_presenceLocatedElement(CSS_SEL_SEARCH_WHAT)
        self.selenium.sendKeys(CSS_SEL_SEARCH_WHAT, what, clear=True)
        self.selenium.sendKeys(CSS_SEL_SEARCH_WHERE, where, clear=True)
        self.selenium.waitAndClick(CSS_SEL_SEARCH_BTN)
        self.selenium.waitUntilPageIsLoaded()

    def clickSortByDate(self):
        self.selenium.waitAndClick(CSS_SEL_SORT_BY_DATE)

    def get_total_results_from_header(self, keywords: str) -> int:
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
        sleep(0.5, 1)
        return True

    @retry(exception=WebDriverException, raiseException=False, exceptionFnc=lambda self, *args, **kwargs: self.close_modal())
    def click_next_page(self):
        sleep(1, 2)
        self.selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON)
        return True

    def close_modal(self):
        modals = self.selenium.getElms(CSS_SEL_JOB_MODAL_CLOSE_BTN)
        if modals:
            self.selenium.waitAndClick(modals[0])

    @retry(exception=ElementClickInterceptedException, exceptionFnc=lambda self, *args, **kwargs: self.close_modal())
    def load_job_detail(self, jobLinkElm: WebElement):
        print(yellow("loading..."), end="")
        sleep(2, 4)
        self.selenium.waitAndClick(jobLinkElm)
        sleep(9, 11)

    def get_job_link_element(self, idx):
        liElm = self.selenium.getElms(CSS_SEL_JOB_LI)[idx]
        return self.selenium.getElmOf(liElm, CSS_SEL_JOB_LINK)

    def get_job_url(self, element: WebElement) -> str:
        return element.get_attribute("href")

    def load_page(self, url: str):
        print(yellow(f"Loading page {url}"))
        self.selenium.loadPage(url)

    def wait_until_page_is_loaded(self):
        self.selenium.waitUntilPageIsLoaded()

    def get_job_data(self):
        title = self.selenium.getText(CSS_SEL_JOB_TITLE).removesuffix("\n- job post")
        company = self.selenium.getText(CSS_SEL_COMPANY)
        location = self.selenium.getText(CSS_SEL_LOCATION)
        html = self.selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
        return title, company, location, html

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

    def back(self):
        self.selenium.back()
