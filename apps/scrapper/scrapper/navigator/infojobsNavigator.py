from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from commonlib.decorator.retry import retry
from commonlib.terminalColor import green, yellow, printHR
from commonlib.stringUtil import join
from ..services.selenium.seleniumService import SeleniumService
from ..services.selenium.browser_service import sleep
from ..selectors.infojobsSelectors import (
    CSS_SEL_JOB_DETAIL, CSS_SEL_SEARCH_RESULT_ITEMS_FOUND, CSS_SEL_COMPANY, CSS_SEL_LOCATION,
    CSS_SEL_JOB_TITLE, CSS_SEL_JOB_LI, CSS_SEL_JOB_LINK, CSS_SEL_NEXT_PAGE_BUTTON, 
    CSS_SEL_SECURITY_FILTER1, CSS_SEL_SECURITY_FILTER2
)


from .baseNavigator import BaseNavigator

class InfojobsNavigator(BaseNavigator):
    @retry(retries=10, delay=5, exception=NoSuchElementException)
    def accept_cookies(self):
        if not self.selenium.usesUndetectedDriver():
            print(yellow('SOLVE A SECURITY FILTER in selenium webbrowser...'), end='')
            sleep(4, 4)
        self.selenium.scrollIntoView('#didomi-notice-agree-button > span')
        sleep(1, 3)
        self.selenium.waitAndClick('#didomi-notice-agree-button > span')
        sleep(2, 4)
        print()

    def security_filter(self):
        if self.selenium.usesUndetectedDriver():
            self.accept_cookies()
            return
        self.selenium.waitUntilPageIsLoaded()
        sleep(4, 4)
        self.selenium.waitAndClick(CSS_SEL_SECURITY_FILTER1)
        self.selenium.waitAndClick(CSS_SEL_SECURITY_FILTER2)
        try:
            self.accept_cookies()
        except NoSuchElementException:
            print(yellow('Could not accept cookies'))
        self.selenium.waitUntilPageUrlContains('https://www.infojobs.net', 60)

    def get_total_results(self, keywords: str) -> int:
        total = self.selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0]
        printHR()
        print(green(join(f'{total} total results for search: {keywords}')))
        printHR()
        return int(total.replace(',', ''))

    def scroll_to_bottom(self):
        """ pre scroll to bottom to force load of li's """
        print("scrollToBottom... ", end='')
        self.selenium.scrollProgressive(600)
        self.selenium.scrollProgressive(-1200)
        sleep(1, 2)

    @retry(retries=5, delay=3, exception=NoSuchElementException, raiseException=False)
    def click_next_page(self):
        """Click on next to load next page."""
        self.selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON)
        return True

    def load_search_page(self):
        if self.selenium.getUrl().find('infojobs.net') == -1:
            print(yellow(f'Loading search-jobs page'))
            self.selenium.loadPage('https://www.infojobs.net/')
            self.selenium.waitUntilPageIsLoaded()
        print(yellow(f'Click on search-jobs button'))
        self.click_on_search_jobs()

    @retry(retries=10, delay=5, exceptionFnc=lambda self, *args, **kwargs: self.security_filter())
    def click_on_search_jobs(self, forcePageLoad=False):
        if (not forcePageLoad) and self.selenium.getUrl().find('/ofertas-trabajo') > 0:
            return
        self.selenium.waitAndClick('header nav ul li a[href="/ofertas-trabajo"]', scrollIntoView=True)
        self.selenium.waitUntilPageIsLoaded()

    def waitForSecurityFilterUserResolved(self):
        print(yellow(f'Waiting for security filter to be resolved'))
        
    @retry(retries=50, delay=2, exceptionFnc=lambda self, *args, **kwargs: self.waitForSecurityFilterUserResolved())
    def load_filtered_search_results(self, keywords: str):
        self.click_on_search_jobs()
        if not self.selenium.sendKeys('.ij-SidebarFilter #fieldsetKeyword', keywords, keyByKeyTime=(0.1, 0.2), clear=True):
            print(yellow('Could not set search keyword, reloading search page'))
            self.click_on_search_jobs(forcePageLoad=True)
            self.selenium.sendKeys('.ij-SidebarFilter #fieldsetKeyword', keywords, keyByKeyTime=(0.1, 0.2))
        sleep(0.5, 1)
        self.selenium.sendEscapeKey()
        sleep(0.5, 1)
        self.selenium.waitAndClick('.ij-SidebarFilter #buttonKeyword', scrollIntoView=True)
        sleep(1, 2)
        self.selenium.waitAndClick('.ij-SidebarFilter input[type="radio"][value="_7_DAYS"]', scrollIntoView=True)
        sleep(1, 2)
        if self.selenium.getElms('.ij-OfferList-NoResults-title').__len__() > 0:
            print(yellow('No results for this search'))
            printHR()
            print()
            return False
        self.selenium.waitAndClick('.ij-SidebarFilter #check-teleworking--2', scrollIntoView=True)
        sleep(1, 2)
        return True

    @retry(retries=3, delay=1, exceptionFnc=lambda self, *args, **kwargs: self.scroll_to_bottom())
    def scroll_jobs_list(self, idx):
        links = self.selenium.getElms(CSS_SEL_JOB_LINK)
        if idx >= len(links):
            for li in self.selenium.getElms(CSS_SEL_JOB_LI)[len(links)-1:]:
                self.selenium.setAttr(li, 'style', (self.selenium.getAttr(li, 'style') or '')+'border: 5px solid red;')
                self.selenium.scrollIntoView(li)
                sleep(0.5, 1)
                self.selenium.setAttr(li, 'style', '')
            sleep(1, 2)
        
        link_elms = self.selenium.getElms(CSS_SEL_JOB_LINK)
        if idx < len(link_elms):
            self.selenium.scrollIntoView(link_elms[idx])

    def get_job_link_element(self, idx) -> WebElement:
        return self.selenium.getElms(CSS_SEL_JOB_LINK)[idx]

    def get_job_url(self, element: WebElement) -> str:
        return element.get_attribute('href')
        
    @retry()
    def click_job_link(self, element: WebElement):
        self.selenium.waitAndClick(element)

    def get_job_data(self):
        title = self.selenium.getText(CSS_SEL_JOB_TITLE)
        company = self.selenium.getText(CSS_SEL_COMPANY)
        location = self.selenium.getText(CSS_SEL_LOCATION)
        html = self.selenium.getHtml(CSS_SEL_JOB_DETAIL)
        url = self.selenium.getUrl()
        return title, company, location, url, html
        


