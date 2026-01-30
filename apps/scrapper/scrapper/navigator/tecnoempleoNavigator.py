from selenium.common.exceptions import NoSuchElementException
from commonlib.decorator.retry import retry
from commonlib.terminalColor import green, yellow, printHR
from commonlib.stringUtil import join
from .baseNavigator import BaseNavigator
from ..services.selenium.browser_service import sleep
from ..services.selenium.seleniumService import SeleniumService



CSS_SEL_SEARCH_RESULT_ITEMS_FOUND = 'div.container div.row div:nth-child(2) h1'
CSS_SEL_MESSAGES_HIDE = 'aside[id="msg-overlay"] header > div.msg-overlay-bubble-header__controls > button'
CSS_SEL_GLOBAL_ALERT_HIDE = 'div.artdeco-global-alert section.artdeco-global-alert__body button.artdeco-global-alert__dismiss'
# LIST
CSS_SEL_NO_RESULTS = 'div.container div.row div:nth-child(2) h3.h4'
CSS_SEL_MAIN_CONTAINER = '#wrapper > div.container > div > div.col-12.col-sm-12.col-md-12.col-lg-9 '
CSS_SEL_JOB_LI = f'{CSS_SEL_MAIN_CONTAINER} > div'
CSS_SEL_JOB_LI_IDX = f'{CSS_SEL_JOB_LI}:nth-child(##idx##) > div > div:nth-child(3)'
CSS_SEL_JOB_LI_IDX_LINK = f'{CSS_SEL_JOB_LI_IDX} > h3 > a'
CSS_SEL_PAGINATION_LINKS = f'{CSS_SEL_MAIN_CONTAINER} > nav > ul > li > a'
# JOB DETAIL
CSS_SEL_JOB_DETAIL = '#wrapper > section.m-0.pt-5 > div:nth-child(1) > div > div.col-12.col-md-7.col-lg-8.mb-5'
CSS_JOB_DETAIL_HEADER = f'{CSS_SEL_JOB_DETAIL} > div.row > div:nth-child(2)'
CSS_SEL_JOB_TITLE = f'{CSS_JOB_DETAIL_HEADER} > div > h1'
CSS_SEL_COMPANY = f'{CSS_JOB_DETAIL_HEADER} > a > span[itemprop=name]'
CSS_SEL_JOB_DESCRIPTION = f'{CSS_SEL_JOB_DETAIL} div[itemprop=description] p'
# Datos principales de la oferta
CSS_SEL_JOB_DATA = '#wrapper > section.m-0.pt-5 > div:nth-child(1) > div > div.col-12.col-md-5.col-lg-4.mb-5 > div > ul > li > span:nth-child(1)'
# CSS_SEL_JOB_EASY_APPLY = f'{CSS_SEL_JOB_DETAIL} div.jobs-details__main-content button.jobs-apply-button svg[data-test-icon="linkedin-bug-xxsmall"]'
# CSS_SEL_JOB_CLOSED = f'{CSS_SEL_JOB_DETAIL} div.jobs-details__main-content div.jobs-details-top-card__apply-error'  # No longer accepting applications

class TecnoempleoNavigator(BaseNavigator):
    
    @retry(retries=10, delay=10)
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
        if self.selenium.usesUndetectedDriver():
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

    def get_total_results(self, keywords: str, remote) -> int:
        total = self.selenium.getText(CSS_SEL_SEARCH_RESULT_ITEMS_FOUND).split(' ')[0]
        printHR(green)
        print(green(join(f'{total} total results for search: {keywords}',
                         f'(remote={remote})')))
        printHR(green)
        return int(total)

    def scroll_to_bottom(self):
        self.selenium.scrollIntoView('nav[aria-label=pagination]')

    @retry(exceptionFnc=lambda self, *args, **kwargs: self.scroll_to_bottom())
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
        html = '\n'.join(['- '+self.selenium.getText(elm) for elm in self.selenium.getElms(CSS_SEL_JOB_DATA)]) + '\n' * 2
        html += self.selenium.getHtml(CSS_SEL_JOB_DESCRIPTION)
        return title, company, location, url, html
    
    def get_attribute(self, css_sel, attr):
        return self.selenium.getAttr(css_sel, attr)
    
    def check_rate_limit(self):
        if self.selenium.getText('div.cf-wrapper header').find('You are being rate limited')>-1:
            return True
        return False
