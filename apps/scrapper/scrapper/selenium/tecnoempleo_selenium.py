from selenium.common.exceptions import NoSuchElementException
from commonlib.decorator.retry import retry
from commonlib.terminalColor import green, yellow, printHR
from commonlib.util import join
from ..seleniumUtil import SeleniumUtil, sleep
from ..selectors.tecnoempleoSelectors import (
    CSS_SEL_JOB_DATA, CSS_SEL_JOB_DESCRIPTION, CSS_SEL_JOB_LI_IDX, CSS_SEL_NO_RESULTS,
    CSS_SEL_SEARCH_RESULT_ITEMS_FOUND, CSS_SEL_JOB_LI_IDX_LINK, CSS_SEL_COMPANY,
    CSS_SEL_JOB_TITLE, CSS_SEL_PAGINATION_LINKS
)

class TecnoempleoNavigator:
    def __init__(self, selenium: SeleniumUtil):
        self.selenium = selenium

    @retry(retries=3, delay=10)
    def wait_for_undetected_security_filter(self):
        self.selenium.waitUntil_presenceLocatedElement('#e_mail', 20)

    @retry(retries=60, delay=5, exception=NoSuchElementException)
    def cloud_flare_security_filter(self):
        print(yellow('SOLVE A SECURITY FILTER in selenium webbrowser...'), end='')
        sleep(4, 4)
        self.selenium.getElm('#e_mail')

    def login(self, user_email, user_pwd):
        sleep(2, 2)
        self.selenium.waitAndClick('nav ul li a[title="Acceso Candidatos"]')
        self.selenium.waitUntilPageIsLoaded()
        if self.selenium.driverUtil.useUndetected:
            self.wait_for_undetected_security_filter()
        else:
            self.cloud_flare_security_filter()
        self.selenium.sendKeys('#e_mail', user_email)
        self.selenium.sendKeys('#password', user_pwd)
        self.selenium.waitAndClick('form input[type=submit]')

    def check_results(self, keywords: str, url: str, remote) -> bool:
        noResultElm = self.selenium.getElms(CSS_SEL_NO_RESULTS)
        if len(noResultElm) > 0:
            print(Exception(
                join('No results for job search on Tecnoempleo for',
                     f'keywords={keywords}', f'remote={remote}',
                     )))
            return False
        return True

    def replace_index(self, cssSelector: str, idx: int):
        return cssSelector.replace('##idx##', str(idx))

    def get_total_results_from_header(self, keywords: str, remote) -> int:
        total = self.selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0]
        printHR(green)
        print(green(join(f'{total} total results for search: {keywords}',
                         f'(remote={remote})')))
        printHR(green)
        return int(total)

    def scroll_to_bottom(self):
        self.selenium.scrollIntoView('nav[aria-label=pagination]')

    @retry(exceptionFnc=lambda self: self.scroll_to_bottom())
    def scroll_jobs_list_retry(self, cssSel):
        self.selenium.scrollIntoView(cssSel)

    def scroll_jobs_list(self, idx):
        cssSel = self.replace_index(CSS_SEL_JOB_LI_IDX, idx)
        self.scroll_jobs_list_retry(cssSel)
        cssSel = self.replace_index(CSS_SEL_JOB_LI_IDX_LINK, idx)
        self.selenium.waitUntilClickable(cssSel)
        return cssSel

    @retry(exception=NoSuchElementException, raiseException=False)
    def click_next_page(self):
        nextPageElms = self.selenium.getElms(CSS_SEL_PAGINATION_LINKS)
        if len(nextPageElms) == 0:
            return False
        nextPageElm = nextPageElms[-1]
        if self.selenium.getText(nextPageElm).isnumeric():
            return False
        self.selenium.waitAndClick(nextPageElm, scrollIntoView=True)
        return True

    def accept_cookies(self):
        sleep(1, 2)
        self.close_create_alert()
        cssSel = '#capa_cookie_rgpd > div.row > div:nth-child(1) > a'
        if len(self.selenium.getElms(cssSel)) > 0:
            self.selenium.waitAndClick(cssSel)

    def close_create_alert(self):
        cssSel = '#wrapper_toast_br > div > div > button > span:nth-child(1)'
        if len(self.selenium.getElms(cssSel)) > 0:
            self.selenium.waitAndClick(cssSel)

    @retry(raiseException=False)
    def load_detail(self, cssSelLink: str):
        self.selenium.waitAndClick(cssSelLink)
        return True

    def get_job_data(self):
        title = self.selenium.getText(CSS_SEL_JOB_TITLE)
        company = self.selenium.getText(CSS_SEL_COMPANY)
        location = ''
        url = self.selenium.getUrl()
        
        # HTML construction from original code
        html = '\\n'.join(['- '+self.selenium.getText(elm) for elm in self.selenium.getElms(CSS_SEL_JOB_DATA)]) + '\\n' * 2
        html += self.selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
        
        return title, company, location, url, html
    
    def get_attribute(self, css_sel, attr):
        return self.selenium.getAttr(css_sel, attr)
    
    def load_page(self, url):
        self.selenium.loadPage(url)
        self.selenium.waitUntilPageIsLoaded()
        
    def wait_until_page_url_contains(self, url, timeout):
        self.selenium.waitUntilPageUrlContains(url, timeout)

    def wait_until_page_is_loaded(self):
        self.selenium.waitUntilPageIsLoaded()
        
    def check_rate_limit(self):
        if self.selenium.getText('div.cf-wrapper header').find('You are being rate limited')>-1:
            return True
        return False
        
    def go_back(self):
        self.selenium.back()
