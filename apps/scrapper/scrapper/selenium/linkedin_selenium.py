from typing import Tuple
from commonlib.decorator.retry import retry
from commonlib.terminalColor import green, yellow, printHR
from commonlib.util import join
from selenium.common.exceptions import NoSuchElementException

from ..baseScrapper import printPage
from ..seleniumUtil import SeleniumUtil, sleep
from ..selectors.linkedinSelectors import (
    CSS_SEL_JOB_DESCRIPTION, CSS_SEL_JOB_EASY_APPLY, CSS_SEL_JOB_HEADER, CSS_SEL_NO_RESULTS,
    CSS_SEL_SEARCH_RESULT_ITEMS_FOUND, CSS_SEL_JOB_LI_IDX, CSS_SEL_COMPANY, CSS_SEL_LOCATION,
    LI_JOB_TITLE_CSS_SUFFIX, CSS_SEL_JOB_LINK, CSS_SEL_NEXT_PAGE_BUTTON, CSS_SEL_MESSAGES_HIDE
)

class LinkedinNavigator:
    def __init__(self, selenium: SeleniumUtil):
        self.selenium = selenium

    def load_page(self, url: str):
        print(yellow(f'Loading page {url}'))
        self.selenium.loadPage(url)
        self.selenium.waitUntilPageIsLoaded()

    def check_login_popup(self, login_callback) -> bool:
        sleep(2, 3)
        if self.selenium.waitAndClick_noError("#base-contextual-sign-in-modal > div > section > div > div > div > div.sign-in-modal > button", "Checking linkedin login popup is present", showException=False):
            login_callback()
            return True
        return False

    def login(self, user_email, user_pwd):
        self.selenium.loadPage('https://www.linkedin.com/login')
        self.selenium.waitUntilPageIsLoaded()
        if self.selenium.getUrl().find('linkedin.com/feed/') > -1:
            return
        self.selenium.sendKeys('#username', user_email)
        self.selenium.sendKeys('#password', user_pwd)
        try:
            self.selenium.checkboxUnselect('div.remember_me__opt_in input')
        except Exception:
            print(yellow('Could not click on "remember me" checkbox'))
        self.selenium.waitAndClick('form button[type=submit]')

    def check_results(self, keywords: str, url: str, remote, location, f_TPR) -> bool:
        noResultElm = self.selenium.getElms(CSS_SEL_NO_RESULTS)
        if len(noResultElm) == 0:
            return True
        print(yellow(
            join('No results for job search on linkedIn for',
                    f'keywords={keywords}', f'remote={remote}',
                    f'location={location}', f'old={f_TPR}', f'URL {url}')))
        return False

    def replace_index(self, cssSelector: str, idx: int):
        return cssSelector.replace('##idx##', str(idx))

    @retry(exception=NoSuchElementException)
    def get_total_results(self, keywords: str, remote, location, f_TPR) -> int:
        total = self.selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0].replace('+', '')
        printHR(green)
        print(green(join(f'{total} total results for search: {keywords}',
                        f'(remote={remote}, location={location}, last={f_TPR})')))
        printHR(green)
        return int(total.replace('+', ''))

    def scroll_jobs_list(self, idx):
        cssSel = self.replace_index(CSS_SEL_JOB_LINK, idx)
        try:
            self.selenium.scrollIntoView(cssSel)
        except NoSuchElementException:
            self.scroll_jobs_list_retry(idx)
            self.selenium.scrollIntoView(cssSel)
        self.selenium.moveToElement(self.selenium.getElm(cssSel))
        self.selenium.waitUntilClickable(cssSel)
        return cssSel

    @retry()
    def scroll_jobs_list_retry(self, idx):
        for i in range(idx, idx+1):
            cssSelI = self.replace_index(CSS_SEL_JOB_LI_IDX, i)
            self.selenium.scrollIntoView(cssSelI)
            self.selenium.moveToElement(self.selenium.getElm(cssSelI))
            self.selenium.waitUntilClickable(self.replace_index(CSS_SEL_JOB_LINK, i))

    @retry(exception=NoSuchElementException, raiseException=False)
    def click_next_page(self):
        self.selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON, scrollIntoView=True)
        return True

    def load_job_detail(self, jobExists: bool, idx: int, cssSel):
        if jobExists or idx == 1:
            return
        print(yellow('loading...'), end='', flush=True)
        self.selenium.waitAndClick(cssSel)

    def get_job_data_in_detail_page(self) -> Tuple[str, str, str, str, str]:
        self.selenium.waitUntilClickable('div.jobs-description > footer > button')
        title = self.selenium.getText('.job-view-layout.jobs-details h1')
        company = self.selenium.getText('.job-view-layout.jobs-details .job-details-jobs-unified-top-card__company-name')
        location = self.selenium.getText('.job-view-layout.jobs-details .job-details-jobs-unified-top-card__primary-description-container > div > span > span:nth-child(1)')
        self.selenium.waitAndClick('div.jobs-description > footer > button') 
        url = self.selenium.getUrl()
        html = self.selenium.getHtml('article div.jobs-box__html-content div.mt4')
        return title, company, location, url, html

    def get_job_data_in_list(self, idx: int) -> Tuple[str, str, str, str, str]:
        liPrefix = self.replace_index(CSS_SEL_JOB_LI_IDX, idx)
        title = self.selenium.getText(f'{liPrefix} {LI_JOB_TITLE_CSS_SUFFIX}')
        company = self.selenium.getText(f'{liPrefix} {CSS_SEL_COMPANY}')
        location = self.selenium.getText(f'{liPrefix} {CSS_SEL_LOCATION}')
        self.selenium.waitUntilClickable(CSS_SEL_JOB_HEADER)
        # Note: URL processing (getJobUrlShort) might be better in Service or Utility, but raw URL comes from here. 
        # I'll return the raw URL here and let Service handle the shortening if it's purely logic. 
        # But wait, the original code called `getJobUrlShort` inside `getJobDataInList`.
        # I will return the raw href and let the caller handle shortening to keep this class focused on DOM.
        url = self.selenium.getAttr(CSS_SEL_JOB_HEADER, 'href')
        html = self.selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
        return title, company, location, url, html

    def get_job_url_from_element(self, cssSel):
        return self.selenium.getAttr(cssSel, 'href')

    def check_easy_apply(self):
        return len(self.selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0
    
    def collapse_messages(self):
        self.selenium.waitAndClick_noError(CSS_SEL_MESSAGES_HIDE, 'Could not collapse messages')

    def wait_until_page_url_contains(self, url, timeout):
        self.selenium.waitUntilPageUrlContains(url, timeout)

    def wait_until_page_is_loaded(self):
        self.selenium.waitUntilPageIsLoaded()
