import random
import time
# import undetected_chromedriver as uc
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from commonlib.decorator.retry import retry
from commonlib.terminalColor import yellow

# Rotating User-Agents to avoid Cloudflare security filter
# TODO: Keep list updated, last update 30/ene/2025
DESKTOP_USER_AGENTS = list(filter(lambda line: len(line) > 0 and not line.startswith('#'), """
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

SCROLL_INTO_VIEW_SCRIPT = "arguments[0].scrollIntoView({ block: 'end',  behavior: 'smooth' });"

class SeleniumUtil:

    driver: webdriver.Remote
    action: webdriver.ActionChains
    defaulTab: str
    tabs = {}


    def __init__(self):
        print('seleniumUtil init')
        print(DESKTOP_USER_AGENTS)
        opts = webdriver.ChromeOptions()
        # opts.add_argument("--start-maximized")
        # opts.add_argument("start-maximized")
        opts.add_argument("--window-size=1920,900")
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
        # userAgent = random.choice(DESKTOP_USER_AGENTS)
        # print(yellow(f'Using user-agent={userAgent}'))
        # opts.add_argument(f"user-agent={userAgent}")
        opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        # driver = uc.Chrome(options=opts)
        self.driver = webdriver.Chrome(options=opts)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.action = webdriver.ActionChains(self.driver)
        print(f'seleniumUtil init driver={self.driver}')
        self.defaulTab = self.driver.current_window_handle

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.exit()

    def exit(self):
        print('Exiting SeleniumUtil, close driver...')
        try:
            if self.driver and self.isDriverAlive():
                self.driver.quit()
            else:
                print('Driver already closed or not alive')
        except Exception as ex:
            print(f'Error closing driver: {ex}')

    def isDriverAlive(self) -> bool:
        try:
            self.driver.current_url
            return True
        except Exception:
            return False

    def tabClose(self, name: str = None):
        try:
            if self.isDriverAlive():
                self.driver.close()
            if name:
                self.tabs.pop(name)
        except Exception as ex:
            print(f'Error closing tab: {ex}')


    def tab(self, name: str = None):
        """Switch or create to tab name. If no name specified switches to default tab."""
        if name is None:
            print(f'SeleniumUtil switching to default tab={self.defaulTab}')
            self.driver.switch_to.window(self.defaulTab)
        elif self.tabs.get(name):
            print(f'SeleniumUtil switching to existing tab: {name}')
            self.driver.switch_to.window(self.tabs[name])
        else:
            print(f'SeleniumUtil creating new tab')
            self.driver.switch_to.new_window('tab')
            self.tabs[name] = self.driver.current_window_handle
            self.waitUntilPageIsLoaded(30)

    @retry()
    def loadPage(self, url: str):
        if not self.isDriverAlive():
            raise Exception('Driver connection lost')
        self.driver.get(url)

    def getUrl(self):
        return self.driver.current_url

    def waitUntilPageUrlContains(self, url: str, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until(
            lambda d: str(d.current_url).find(url) >= 0)

    def getElm(self, cssSel: str | WebElement):
        if isinstance(cssSel, WebElement):
            return cssSel
        return self.driver.find_element(By.CSS_SELECTOR, cssSel)

    def getElmOf(self, elm: WebElement, cssSel: str):
        return elm.find_element(By.CSS_SELECTOR, cssSel)

    def getElms(self, cssSel: str, driverOverride=None) -> List[WebElement]:
        if driverOverride:
            return driverOverride.find_elements(By.CSS_SELECTOR, cssSel)
        return self.driver.find_elements(By.CSS_SELECTOR, cssSel)

    def sendEscapeKey(self):
        webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

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
            self.driver.execute_script("arguments[0].click();", checkbox)

    def waitUntilPageIsLoaded(self, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until(
            lambda driver: driver.execute_script(
                'return document.readyState;') == 'complete')

    def scrollToBottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def scrollIntoView(self, cssSel: str | WebElement):
        elm = self.getElmFromOpSelector(cssSel)
        self.driver.execute_script(SCROLL_INTO_VIEW_SCRIPT, elm)
        self.waitUntilVisible(elm)
        self.moveToElement(elm)
    
    def waitUntilClickable(self, cssSel: str | WebElement, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable, self.getElmFromOpSelector(cssSel))

    def waitUntilVisible(self, cssSel: str | WebElement, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until(EC.visibility_of, self.getElmFromOpSelector(cssSel))

    def waitUntil_presenceLocatedElement(self, cssSel: str | WebElement, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located, self.getElmFromOpSelector(cssSel))

    def waitUntilTitleIs(self, title: str, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until(EC.title_is, title)

    def waitAndClick(self, cssSel: str | WebElement, timeout: int = 10, scrollIntoView: bool = False):
        """ scrollIntoView, waits to be clickable & click"""
        if scrollIntoView:
            self.scrollIntoView(cssSel)
        self.waitUntilClickable(cssSel, timeout)
        elm = self.getElmFromOpSelector(cssSel)
        self.moveToElement(elm)
        elm.click()

    def getElmFromOpSelector(self, cssSel: str | WebElement) -> WebElement:
        return self.getElm(cssSel) if isinstance(cssSel, str) else cssSel

    def waitAndClick_noError(self, cssSel: str, msg: str, showException=True) -> bool:
        try:
            self.waitAndClick(cssSel)
            return True
        except Exception as ex:
            if showException:
                print(f'{msg}, exception {ex}')
            else:
                print(f'{msg}')
            return False

    def scrollIntoView_noError(self, cssSel: str | WebElement):
        try:
            self.scrollIntoView(cssSel)
            return True
        except Exception:
            print(yellow(f'scrollIntoView_noError, {cssSel} not Found'), end='')
            return False

    def moveToElement(self, elm: str | WebElement):
        self.action.move_to_element(self.getElmFromOpSelector(elm))
        self.action.perform()

    def getHtml(self, cssSel: str) -> str:
        return self.getAttr(cssSel, 'innerHTML')

    def getText(self, cssSel: str | WebElement) -> str:
        return self.getElm(cssSel).text

    def getAttr(self, cssSel: str, attr: str) -> str:
        return self.getElm(cssSel).get_attribute(attr)

    def getAttrOf(self, elm: WebElement, cssSel: str, attr: str) -> str:
        return self.getElmOf(elm, cssSel).get_attribute(attr)

    def back(self):
        self.driver.back()

    def cloudFlareSecurityFilter(self):
        #TODO Don't detect iframe
        sleep(20,20)
        self.waitUntilPageIsLoaded(30)
        # iframe:WebElement = self.driver.find_elements(By.XPATH,'//iframe')[0]
        self.driver.switch_to.frame(0)
        self.waitAndClick('input[type="checkbox"]')
        self.driver.switch_to.default_content()
        sleep(10,10)


def sleep(ini: float, end: float, disable=False):
    if disable:
        return
    time.sleep(random.uniform(ini, end))


