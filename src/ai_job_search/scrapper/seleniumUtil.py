import random
import time
from typing import List
from selenium import webdriver
# TODO: import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from ai_job_search.tools.terminalColor import yellow

# Rotating User-Agents to avoid Cloudflare security filter
# TODO: Keep list updated, last update 30/ene/2025
DESKTOP_USER_AGENTS = list(
    filter(lambda line: len(line) > 0 and not line.startswith('#'), """
# Chrome
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
# Mozilla Firefox
Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0
Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0
Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0
# Microsoft Edge
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0
# Safari
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15
# Opera
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/120.0.0.0
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/120.0.0.0
""".split('\n')))

driver = None
action = None


class SeleniumUtil:

    def __init__(self):
        global driver, action
        print('selenium driver init')
        print(DESKTOP_USER_AGENTS)
        opts = webdriver.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument("start-maximized")
        # TODO: Couldn't avoid Security filters for Infojobs & Glassdoor
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # options.add_experimental_option('useAutomationExtension', False)
        # driver = webdriver.Chrome(options=options)  # , executable_path=r'C:\WebDrivers\chromedriver.exe')
        # driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36'})
        # print(driver.execute_script("return navigator.userAgent;"))

        # https://www.zenrows.com/blog/selenium-avoid-bot-detection#disable-automation-indicator-webdriver-flags
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        userAgent = random.choice(DESKTOP_USER_AGENTS)
        print(yellow(f'Using user-agent={userAgent}'))
        opts.add_argument(f"user-agent={userAgent}")
        driver = webdriver.Chrome(options=opts)
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        action = webdriver.ActionChains(driver)
        print(f'selenium driver init driver={driver}')

    def loadPage(self, url: str):
        driver.get(url)

    def getUrl(self):
        return driver.current_url

    def waitUntilPageUrlContains(self, url: str, timeout: int = 10):
        WebDriverWait(driver, timeout).until(
            lambda d: str(d.current_url).find(url) >= 0)

    def getElm(self, cssSel: str | WebElement):
        if isinstance(cssSel, WebElement):
            return cssSel
        return driver.find_element(By.CSS_SELECTOR, cssSel)

    def getElmOf(self, elm: WebElement, cssSel: str):
        return elm.find_element(By.CSS_SELECTOR, cssSel)

    def getElms(self, cssSel: str, driverOverride=None) -> List[WebElement]:
        if driverOverride:
            return driverOverride.find_elements(By.CSS_SELECTOR, cssSel)
        return driver.find_elements(By.CSS_SELECTOR, cssSel)

    def sendKeys(self, cssSel: str, value: str,
                 keyByKeyTime: None | tuple[int] = None, clear=True):
        elm = self.getElm(cssSel)
        self.moveToElement(elm)
        if clear:
            elm.clear()
        if keyByKeyTime:
            for c in value:
                elm.send_keys(c)
                sleep(*keyByKeyTime)
        else:
            elm.send_keys(value)

    def checkboxUnselect(self, cssSel: str):
        checkbox = self.getElm(cssSel)
        self.moveToElement(checkbox)
        if checkbox.is_selected():
            driver.execute_script("arguments[0].click();", checkbox)

    def waitUntilPageIsLoaded(self, timeout: int = 10):
        WebDriverWait(driver, timeout).until(
            lambda driver: driver.execute_script(
                'return document.readyState;') == 'complete')

    def scrollIntoView(self, cssSel: str | WebElement):
        elm = self.getElm(cssSel) if isinstance(cssSel, str) else cssSel
        driver.execute_script("arguments[0].scrollIntoView();", elm)
        self.moveToElement(elm)

    def waitUntilClickable(self, cssSel: str | WebElement, timeout: int = 10):
        method = EC.element_to_be_clickable
        WebDriverWait(driver, timeout).until(method, self.getElm(cssSel))

    def waitUntil_presenceLocatedElement(self, cssSel: str, timeout: int = 10):
        method = EC.presence_of_element_located
        WebDriverWait(driver, timeout).until(method, self.getElm(cssSel))

    def waitUntilTitleIs(self, title: str, timeout: int = 10):
        method = EC.title_is
        WebDriverWait(driver, timeout).until(method, title)

    def waitAndClick(self, cssSel: str | WebElement, timeout: int = 10,
                     scrollIntoView: bool = False):
        """ scrollIntoView, waits to be clickable & click"""
        if scrollIntoView:
            self.scrollIntoView(cssSel)
        self.waitUntilClickable(cssSel, timeout)
        elm = self.getElm(cssSel)
        self.moveToElement(elm)
        elm.click()

    def waitAndClick_noError(self, cssSel: str, msg: str, showException=True):
        try:
            self.waitAndClick(cssSel)
        except Exception as ex:
            if showException:
                print(f'{msg}, exception {ex}')
            else:
                print(f'{msg}')

    def scrollIntoView_noError(self, cssSel: str | WebElement):
        try:
            self.scrollIntoView(cssSel)
            return True
        except Exception:
            print(
                yellow(f'scrollIntoView_noError, {cssSel} not Found'), end='')
            return False

    def moveToElement(self, elm: WebElement):
        action.move_to_element(elm)
        action.perform()

    def waitUntilFoundMany(self, cssSel: str, items: int, concept: str = '',
                           timeout: int = 5, retry: int = 4):
        while True:
            try:
                WebDriverWait(driver, timeout).until(
                    lambda d: len(self.getElms(cssSel, d)) == items)
            except TimeoutException as ex:
                found = len(self.getElms(cssSel))
                print(
                    f'waitUntilFound: {concept}, len after exception: {found}')
                if retry > 1:
                    # FIXME: implement as decorator:
                    # https://github.com/indently/five_decorators/blob/main/decorators/001_retry.py
                    print(f'waitUntilFound {concept} retrying...')
                    retry -= 1
                else:
                    raise ex

    def getHtml(self, cssSel: str) -> str:
        return self.getAttr(cssSel, 'innerHTML')

    def getText(self, cssSel: str) -> str:
        return self.getElm(cssSel).text

    def getAttr(self, cssSel: str, attr: str) -> str:
        return self.getElm(cssSel).get_attribute(attr)

    def getAttrOf(self, elm: WebElement, cssSel: str, attr: str) -> str:
        return self.getElmOf(elm, cssSel).get_attribute(attr)

    def back(self):
        driver.back()

    def close(self):
        driver.quit()


def sleep(ini: float, end: float, disable=False):
    if disable:
        return
    time.sleep(random.uniform(ini, end))
