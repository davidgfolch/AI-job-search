from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from scrapper.core.utils import sleep
from scrapper.services.selenium.seleniumSocketConnRetry import seleniumSocketConnRetry

class BrowserService:
    def __init__(self, driver: webdriver.Remote):
        self.driver = driver
        self.default_tab = driver.current_window_handle
        self.tabs = {}

    @seleniumSocketConnRetry()
    def tabClose(self, name: Optional[str] = None):
        try:
            self.driver.close()
            if name and name in self.tabs:
                self.tabs.pop(name)
        except Exception as ex:
            print(f'Error closing tab: {ex}')

    @seleniumSocketConnRetry()
    def tab(self, name: Optional[str] = None):
        """Switch or create to tab name. If no name specified switches to default tab."""
        if name is None:
            print(f'SeleniumUtil switching to default tab={self.default_tab}')
            self.driver.switch_to.window(self.default_tab)
        elif self.tabs.get(name):
            print(f'SeleniumUtil switching to existing tab: {name}')
            self.driver.switch_to.window(self.tabs[name])
        else:
            print(f'SeleniumUtil creating new tab')
            self.driver.switch_to.new_window('tab')
            self.tabs[name] = self.driver.current_window_handle
            self.waitUntilPageIsLoaded(30)

    @seleniumSocketConnRetry()
    def loadPage(self, url: str):
        self.driver.get(url)

    @seleniumSocketConnRetry()
    def getUrl(self):
        return self.driver.current_url

    @seleniumSocketConnRetry()
    def waitUntilPageUrlContains(self, url: str, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until(
            lambda d: str(d.current_url).find(url) >= 0)

    @seleniumSocketConnRetry()
    def waitUntilPageIsLoaded(self, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until(
            lambda driver: driver.execute_script('return document.readyState;') == 'complete')

    @seleniumSocketConnRetry()
    def sendEscapeKey(self):
        webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

    @seleniumSocketConnRetry()
    def scrollProgressive(self, distance: int):
        currentPos = self.driver.execute_script("return window.pageYOffset;")
        targetPos = currentPos + distance
        step = 50 if distance > 0 else -50
        while (step > 0 and currentPos < targetPos) or (step < 0 and currentPos > targetPos):
            currentPos += step
            if (step > 0 and currentPos > targetPos) or (step < 0 and currentPos < targetPos):
                currentPos = targetPos
            self.driver.execute_script(f"window.scrollTo(0, {currentPos});")
            sleep(0.01, 0.03)
        self.driver.execute_script(f"window.scrollTo(0, {targetPos});")

    @seleniumSocketConnRetry()
    def back(self):
        self.driver.back()
