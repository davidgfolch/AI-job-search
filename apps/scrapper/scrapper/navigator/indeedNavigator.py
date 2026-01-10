from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from commonlib.decorator.retry import retry
from commonlib.terminalColor import green, yellow, printHR
from commonlib.stringUtil import join
from ..services.selenium.seleniumService import SeleniumService
from ..services.selenium.browser_service import sleep
from ..selectors.indeedSelectors import (
    CSS_SEL_JOB_DESCRIPTION,
    CSS_SEL_JOB_EASY_APPLY,
    CSS_SEL_JOB_LI,
    CSS_SEL_JOB_REQUIREMENTS,
    CSS_SEL_SEARCH_RESULT_ITEMS_FOUND,
    CSS_SEL_COMPANY,
    CSS_SEL_LOCATION,
    CSS_SEL_JOB_TITLE,
    CSS_SEL_JOB_LINK,
    CSS_SEL_NEXT_PAGE_BUTTON)


class IndeedNavigator:
    def __init__(self, selenium: SeleniumService):
        self.selenium = selenium

    def accept_cookies(self):
        self.selenium.waitAndClick_noError(
            '#onetrust-accept-btn-handler', 'Could not accept cookies')

    def get_total_results_from_header(self, keywords: str) -> int:
        try:
            total = self.selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0]
            printHR()
            print(green(join(f'{total} total results for search: {keywords}')))
            printHR()
            # Clean up potential separators
            return int(total.replace('.', '').replace(',', ''))
        except Exception:
            print(yellow(f'Could not get total results for {keywords}'))
            return 0

    def scroll_jobs_list(self, idx):
        li = self.selenium.getElms(CSS_SEL_JOB_LI)[idx]
        self.selenium.scrollIntoView_noError(li)
        sleep(0.5, 1)

    @retry(exception=NoSuchElementException, raiseException=False)
    def click_next_page(self):
        """Click on next to load next page.
        If there isn't next button in pagination we are in the last page,
        so return false to exit loop (stop processing)"""
        sleep(1, 2)
        self.selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON)
        return True

    def load_job_detail(self, jobLinkElm: WebElement):
        print(yellow('loading...'), end='')
        sleep(2, 4)
        self.selenium.waitAndClick(jobLinkElm)
        sleep(9, 11)

    def get_job_link_element(self, idx):
        liElm = self.selenium.getElms(CSS_SEL_JOB_LI)[idx]
        return self.selenium.getElmOf(liElm, CSS_SEL_JOB_LINK)

    def get_job_url(self, element: WebElement) -> str:
        return element.get_attribute('href')

    def load_page(self, url: str):
        print(yellow(f'Loading page {url}'))
        self.selenium.loadPage(url)

    def wait_until_page_is_loaded(self):
        self.selenium.waitUntilPageIsLoaded()

    def get_job_data(self):
        title = self.selenium.getText(CSS_SEL_JOB_TITLE).removesuffix('\n- job post')
        company = self.selenium.getText(CSS_SEL_COMPANY)
        location = self.selenium.getText(CSS_SEL_LOCATION)
        self.selenium.scrollIntoView(CSS_SEL_JOB_REQUIREMENTS)
        sleep(1, 2)
        self.selenium.waitUntil_presenceLocatedElement(CSS_SEL_JOB_REQUIREMENTS)
        html = self.selenium.getHtml(CSS_SEL_JOB_REQUIREMENTS)
        html += self.selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)

        return title, company, location, html

    def check_easy_apply(self):
        return len(self.selenium.getElms(CSS_SEL_JOB_EASY_APPLY)) > 0
    
    def back(self):
        self.selenium.back()
