import re
from typing import Tuple
from commonlib.decorator.retry import retry
from commonlib.exceptionUtil import try_or_warn
from commonlib.observability import get_logger
from commonlib.stringUtil import join
from commonlib.terminalColor import green, yellow, printHR
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

from ..services.selenium.seleniumService import SeleniumService
from ..services.selenium.browser_service import sleep

from .baseNavigator import BaseNavigator
from .components.linkedinDetailReader import LinkedinDetailReader

logger = get_logger("scrapper.linkedinNavigator")

JOB_CARD_CK_RE = r'job-card-component-ref-(\d+)'  # componentkey carries the job id


def job_id_from_componentkey(componentkey: str) -> str:
    match = re.search(JOB_CARD_CK_RE, componentkey or '')
    if not match:
        raise NoSuchElementException(f'No job id in componentkey {componentkey}')
    return match.group(1)

CSS_SEL_LOGIN_USER = 'input[type=email]'
CSS_SEL_LOGIN_PWD = 'input[type=password]'
CSS_SEL_LOGIN_BUTTON = 'button[type=button]'  # login form is rendered twice, the submit is the last button of the last copy
CSS_SEL_LOGIN_BUTTON_LEGACY = 'button[type=submit]'
# "keep me signed in" is a custom ARIA toggle: classes are hashed, aria-label is localized, so match on role/aria-checked
CSS_SEL_LOGIN_REMEMBER_ME = 'div[role=checkbox][aria-checked="true"]'
CSS_SEL_SEARCH_RESULT_ITEMS_FOUND = 'main header div[componentkey=searchResultsHeaderComponent] p'
CSS_SEL_MESSAGES_HIDE = 'aside#msg-overlay div.msg-overlay-bubble-header__controls button:last-child'
CSS_SEL_GLOBAL_ALERT_HIDE = 'section.artdeco-global-alert__body button:first-child'
# LIST: cards are role=button divs, listed in visual order
CSS_SEL_JOB_CARD = 'div[role=button][componentkey^=job-card-component-ref-]'
CSS_SEL_NEXT_PAGE_BUTTON = 'div[componentkey=SearchResultsMainContent] > div:has(> ul > li > button[aria-label]) > button:last-child'

class LinkedinNavigator(BaseNavigator):

    def __init__(self, selenium: SeleniumService, debug: bool):
        super().__init__(selenium, debug)
        self.detail_reader = LinkedinDetailReader(selenium)

    def check_login_popup(self, login_callback) -> bool:
        sleep(2, 3)
        if self.selenium.waitAndClick_noError("#base-contextual-sign-in-modal > div > section > div > div > div > div.sign-in-modal > button", "Checking linkedin login popup is present", showException=False):
            login_callback()
            return True
        return False

    @retry()
    def login(self, user_email, user_pwd):
        self.selenium.loadPage('https://www.linkedin.com/login')
        self.selenium.waitUntilPageIsLoaded(30)
        if self.selenium.getUrl().find('linkedin.com/feed/') > -1:
            return
        sleep(1, 1)
        self.selenium.waitUntil_presenceLocatedElement(CSS_SEL_LOGIN_USER)
        self.selenium.waitUntil_presenceLocatedElement(CSS_SEL_LOGIN_PWD)
        user_elms = self.selenium.getElms(CSS_SEL_LOGIN_USER)
        pwd_elms = self.selenium.getElms(CSS_SEL_LOGIN_PWD)
        if not user_elms or not pwd_elms:
            raise Exception('Login form elements not found')
        self.selenium.sendKeys(user_elms.pop(), user_email)
        self.selenium.sendKeys(pwd_elms.pop(), user_pwd)
        self.uncheck_remember_me()
        self.loginSubmit()

    def uncheck_remember_me(self):
        elms = self.selenium.getElms(CSS_SEL_LOGIN_REMEMBER_ME)
        if not elms:
            logger.info("linkedin.login.remember_me_absent", console=yellow('"Remember me" checkbox not found or already unchecked'))
            return
        try_or_warn(lambda: self.selenium.checkboxUnselect(elms.pop()), 'Could not uncheck "remember me" checkbox')

    @retry()
    def loginSubmit(self):
        """LinkedIn used to submit with button[type=submit], nowadays the whole form is a JS widget whose last button submits"""
        for cssSel in (CSS_SEL_LOGIN_BUTTON_LEGACY, CSS_SEL_LOGIN_BUTTON):
            elms = self.selenium.getElms(cssSel)
            if elms:
                self.selenium.waitAndClick(elms.pop())
                return
        raise Exception('Login submit button not found')


    def check_redirected_to_login(self, login_callback) -> bool:
        current_url = self.selenium.getUrl()
        if any(p in current_url for p in ['linkedin.com/login', 'linkedin.com/uas/login', 'linkedin.com/authwall']):
            logger.warning("linkedin.auth.redirect_to_login", console=yellow("Detected redirect to login page, re-logging in..."))
            login_callback()
            return True
        return False

    def close_cookies_banner(self):
        self.selenium.waitAndClick_noError(CSS_SEL_GLOBAL_ALERT_HIDE, 'Could not close cookies banner')

    def check_results(self, keywords: str, url: str, remote, location, f_TPR) -> bool:
        # LinkedIn dropped the no-results banner: an empty search serves a "0 results" header instead
        try:
            total = self.selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).strip()
        except NoSuchElementException:
            return True  # header not rendered yet: get_total_results retries and fails loudly if the layout changed
        if total.startswith('0'):
            logger.info("linkedin.no_results", keywords=keywords, remote=remote, location=location, last=f_TPR, url=url,
                        console=yellow(join('No results for job search on linkedIn for', f'keywords={keywords}', f'remote={remote}', f'location={location}', f'old={f_TPR}', f'URL {url}')))
            return False
        return True

    @retry(exception=NoSuchElementException)
    def get_total_results(self, keywords: str, remote, location, f_TPR, sortBy) -> int:
        total = self.selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0].replace('+', '')
        printHR(green)
        logger.info("linkedin.results_found", total=total, keywords=keywords, remote=remote, location=location, last=f_TPR, sort_by=sortBy,
                    console=green(join(f'{total} total results for search: {keywords}', f'(remote={remote}, location={location}, last={f_TPR}, sortBy={sortBy})')))
        printHR(green)
        return int(total.replace('+', ''))

    def scroll_jobs_list(self, idx) -> WebElement:
        cards = self._get_cards(idx)
        elm = cards[idx - 1]
        self.selenium.scrollIntoView(elm, block='center')  # the fixed div covers the viewport bottom: a block=end card would sit under it
        self.selenium.moveToElement(elm)
        self.selenium.waitUntilClickable(elm)
        return elm

    def _get_cards(self, idx: int) -> list[WebElement]:
        cards = []
        for _ in range(10):  # list may still be rendering after a page load / pagination click
            cards = self.selenium.getElms(CSS_SEL_JOB_CARD)
            if len(cards) >= idx:
                return cards
            sleep(0.5, 0.8)
        raise NoSuchElementException(f'Job card {idx} not found (page has {len(cards)})')

    @retry(exception=(NoSuchElementException, ElementClickInterceptedException), raiseException=False)
    def click_next_page(self):
        self.selenium.scrollIntoView(CSS_SEL_NEXT_PAGE_BUTTON)
        self.selenium.scrollContainerToBottom(CSS_SEL_NEXT_PAGE_BUTTON)  # the list is a nested scrollbox the document never scrolls: its own container must hit bottom so a position:fixed div clears the button
        self.selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON)
        return True

    def load_job_detail(self, jobExists: bool, elm: WebElement):
        if jobExists:
            return
        print(yellow('loading...'), end='', flush=True)
        componentkey = self.selenium.getAttr(elm, 'componentkey')
        expected_job_id = job_id_from_componentkey(componentkey)
        last_interception = None
        for attempt in range(3):
            card = elm if attempt == 0 else self.selenium.getElm(f'{CSS_SEL_JOB_CARD}[componentkey="{componentkey}"]')  # list can re-render between attempts
            self.selenium.scrollIntoView(card, block='center')
            try:
                self.selenium.waitAndClick(card)
            except ElementClickInterceptedException as e:
                last_interception = e  # something overlapped the card: re-scroll and retry
                continue
            if self.detail_reader.wait_for_job(expected_job_id):
                return
        raise NoSuchElementException(f'Job detail pane never showed job {expected_job_id}') from last_interception

    def get_job_data(self) -> Tuple[str, str, str, str, str]:
        return self.detail_reader.read()

    def get_job_url_from_element(self, elm: WebElement) -> str:
        componentkey = self.selenium.getAttr(elm, 'componentkey')
        return f'https://www.linkedin.com/jobs/view/{job_id_from_componentkey(componentkey)}/'

    def check_easy_apply(self):
        return self.detail_reader.check_easy_apply()

    def collapse_messages(self):
        elms = self.selenium.getElms(CSS_SEL_MESSAGES_HIDE)
        if len(elms) > 0:
            self.selenium.waitAndClick_noError(elms[-1], 'Could not collapse messages')
        else:
            logger.info("linkedin.messages.none", console=yellow('No messages found to collapse'))

    def wait_until_page_url_contains(self, url, timeout):
        self.selenium.waitUntilPageUrlContains(url, timeout)
