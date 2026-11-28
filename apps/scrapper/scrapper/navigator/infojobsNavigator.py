from urllib.parse import quote
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.remote.webelement import WebElement
from commonlib.decorator.retry import retry
from commonlib.observability import get_logger
from commonlib.stringUtil import join
from commonlib.terminalColor import green, yellow, printHR
from ..services.selenium.browser_service import sleep
from .baseNavigator import BaseNavigator

logger = get_logger("scrapper.infojobsNavigator")

LOGIN_PAGE = 'https://www.infojobs.net/candidate/candidate-login/candidate-login.xhtml'
SEARCH_URL = 'https://www.infojobs.net/ofertas-trabajo'
# Cookie consent and the "Prime for push" layer are fixed full-viewport overlays: they swallow clicks on the search link, filters and offer cards.
# The consent click is done in JS because the popup is injected after page load and physical clicks on it are unreliable with undetected Chrome.
OVERLAY_REMOVE_SCRIPT = "const b=document.querySelector('#didomi-notice-agree-button > span'); if(b)b.click(); document.querySelectorAll('#didomi-host, iframe[title=\"Prime for push\"], .push-wrapper').forEach(e => e.remove()); document.body.classList.remove('didomi-popup-open')"

CSS_SEL_SECURITY_FILTER1 = 'body > div > div > div > div > div > div > p:nth-child(3) > span.break > a'
# CSS_SEL_SECURITY_FILTER1 = 'body > div > div > div > div > div > div > p:nth-child(3) > span.break > a'
CSS_SEL_SECURITY_FILTER1 = '#captcha-box span.geetest_radar_tip_content'
CSS_SEL_SECURITY_FILTER2 = '#captcha-box > div > div.geetest_wait'

CSS_SEL_SEARCH_RESULT_ITEMS_FOUND = 'div.ij-TemplateAdsPage-mainContainer div.ij-SearchListingPageContent-heading div.ij-Box.ij-SearchListingPageContent-heading-title h1'
CSS_SEL_GLOBAL_ALERT_HIDE = 'div.ij-SearchListingPageContent-heading h1'

# LIST
# Note: there are some li with advertisements, they don't have the ij-OfferCardContent-description-title-link class'
CSS_SEL_JOB_LI = 'div.ij-SearchListingPageContent-list ul li.ij-List-item'
CSS_SEL_JOB_LINK = CSS_SEL_JOB_LI + ' div.ij-OfferCardContent h2 > a'
CSS_SEL_NEXT_PAGE_BUTTON = 'div.ij-Box.ij-SearchListingPageContent-main div.ij-Box.ij-TemplateAdsPage-row.ij-SearchListingPageContent-list div.ij-Box.ij-TemplateAdsPage-row div.ij-ComponentPagination ul.sui-MoleculePagination li.sui-MoleculePagination-item:last-child button.sui-AtomButton.sui-AtomButton--primary.sui-AtomButton--flat.sui-AtomButton--center'

# JOB DETAIL (IN LIST CLICK)
CSS_SEL_JOB_TITLE = 'h1'  # '#prefijoPuesto'
CSS_SEL_COMPANY = '.ij-OfferDetailHeader-companyLogo .ij-OfferDetailHeader-companyLogo-title .ij-OfferDetailHeader-companyLogo-companyName > a' # '#main-wrapper div.heading-addons a.link'
DETAILS_PREFIX = '.ij-OfferDetailHeader-detailsList'
CSS_SEL_LOCATION = 'div.ij-OfferDetailHeader-detailsList-column:nth-child(1) > div:nth-child(1) > p:nth-child(2)'  # '#main-wrapper div.heading-addons a.link'

CSS_SEL_JOB_DETAIL = '.ij-OfferDetailPage-mainContent-container'
# DONT WORK '.ij-OfferDetailPage-mainContent-container > article:not(.ij-OfferDetailFooter)'
CSS_SEL_JOB_CLOSED = f'{CSS_SEL_JOB_DETAIL} div.jobs-details__main-content div.jobs-details-top-card__apply-error'


def build_search_url(keywords: str) -> str:
    """InfoJobs replaced the sidebar keyword field with a top search bar in Nov 2026; the keyword is now a URL parameter."""
    return f'{SEARCH_URL}?keyword={quote(keywords, safe="")}'


class InfojobsNavigator(BaseNavigator):
    @retry(retries=10, delay=5, exception=NoSuchElementException)
    def accept_cookies(self):
        if not self.selenium.usesUndetectedDriver():
            print(yellow('SOLVE A SECURITY FILTER in selenium webbrowser...'), end='')
            sleep(4, 4)
        self.selenium.waitAndClick_noError('div.push-actions #reject-button', "Reject send notifications")
        self.selenium.scrollIntoView_noError('#didomi-notice-agree-button > span')
        sleep(1, 3)
        self.selenium.waitAndClick_noError('#didomi-notice-agree-button > span', "Accept cookies")
        sleep(2, 4)
        print()

    def dismiss_overlays(self):
        """Remove the consent/push layers before any click they could intercept."""
        self.selenium.driver.execute_script(OVERLAY_REMOVE_SCRIPT)

    def security_filter(self):
        if self.selenium.usesUndetectedDriver():
            self.accept_cookies()
            self.dismiss_overlays()
            return
        self.selenium.waitUntilPageIsLoaded()
        sleep(4, 4)
        self.selenium.waitAndClick(CSS_SEL_SECURITY_FILTER1)
        self.selenium.waitAndClick(CSS_SEL_SECURITY_FILTER2)
        try:
            self.accept_cookies()
        except NoSuchElementException:
            logger.warning("infojobs.cookies.not_accepted", console=yellow('Could not accept cookies'))
        self.dismiss_overlays()
        self.selenium.waitUntilPageUrlContains('https://www.infojobs.net', 60)

    def get_total_results(self, keywords: str) -> int:
        total = self.selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0]
        printHR()
        logger.info("infojobs.results_found", total=total, keywords=keywords, console=green(join(f'{total} total results for search: {keywords}')))
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
        self.dismiss_overlays()
        self.selenium.waitAndClick(CSS_SEL_NEXT_PAGE_BUTTON)
        return True

    def load_search_page(self):
        if SEARCH_URL not in self.selenium.getUrl():
            logger.info("infojobs.search.page_loading", console='Loading search-jobs page')
            self.selenium.loadPage(SEARCH_URL)
            self.selenium.waitUntilPageIsLoaded()
        self.dismiss_overlays()

    def load_search_results(self, keywords: str):
        """Load the keyword search directly: the removed sidebar field made sendKeys + submit time out."""
        url = build_search_url(keywords)
        logger.info("infojobs.search.url_loading", keywords=keywords, url=url, console='Loading keyword search results')
        self.selenium.loadPage(url)
        self.selenium.waitUntilPageIsLoaded()
        self.dismiss_overlays()
        self.selenium.waitUntil_presenceLocatedElement_noError(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND, 10)

    def clickOptionalFilter(self, cssSel: str, name: str):
        """A filter click that times out must not restart the whole search and re-enter the keyword."""
        try:
            self.dismiss_overlays()
            self.selenium.waitAndClick(cssSel, scrollIntoView=True)
        except TimeoutException:
            logger.warning("infojobs.filter.click_timeout", filter=name, console=yellow(f'Could not apply {name} filter, continuing'))

    @retry(retries=3, delay=2, exceptionFnc=lambda self, *args, **kwargs: self.waitForSearchReady())
    def load_filtered_search_results(self, keywords: str):
        self.load_search_results(keywords)
        sleep(1, 2)
        self.clickOptionalFilter('.ij-SidebarFilter input[type="radio"][value="_7_DAYS"]', 'last 7 days')
        sleep(1, 2)
        if self.selenium.getElms('.ij-OfferList-NoResults-title').__len__() > 0:
            logger.info("infojobs.no_results", keywords=keywords, console=yellow(f'No results for keyword={keywords}'))
            printHR()
            print()
            return False
        self.filterByRemote()
        return True

    def waitForSearchReady(self):
        logger.warning("infojobs.search.retrying", console=yellow('Retrying InfoJobs search setup after an error'))
        self.dismiss_overlays()

    def filterByRemote(self):
        if len(self.selenium.getElms('.ij-SidebarFilter #check-teleworking--2')) > 0:
            self.clickOptionalFilter('.ij-SidebarFilter #check-teleworking--2', 'remote')
            sleep(1, 2)

    @retry(retries=3, delay=1, exceptionFnc=lambda self, *args, **kwargs: self.scroll_to_bottom())
    def scroll_jobs_list(self, idx):
        links = self.selenium.getElms(CSS_SEL_JOB_LINK)
        if idx >= len(links):
            for li in self.selenium.getElms(CSS_SEL_JOB_LI)[len(links)-1:]:
                # InfoJobs omits style on fresh cards; getAttr() raises on a missing/empty value, so read it tolerantly.
                style = li.get_attribute('style') or ''
                self.selenium.setAttr(li, 'style', style+'border: 5px solid red;')
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
        """Navigate to the offer URL: physical clicks land on overlays that reappear after going back."""
        self.load_page(self.get_job_url(element))

    def go_back(self):
        super().go_back()
        self.selenium.waitUntilPageIsLoaded()
        self.dismiss_overlays()

    def get_job_data(self):
        title = self.selenium.getText(CSS_SEL_JOB_TITLE)
        company = self.selenium.getText(CSS_SEL_COMPANY)
        location = self.selenium.getText(CSS_SEL_LOCATION)
        html = self.selenium.getHtml(CSS_SEL_JOB_DETAIL)
        url = self.selenium.getUrl()
        return title, company, location, url, html
