import random
import time
import traceback
from typing import List, Optional
from scrapper.driverUtil import DriverUtil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from commonlib.decorator.retry import retry
from commonlib.terminalColor import red, yellow
from commonlib.util import isMacOS

SCROLL_INTO_VIEW_SCRIPT = "arguments[0].scrollIntoView({ block: 'end',  behavior: 'smooth' });"

class SeleniumUtil:

    driverUtil: DriverUtil
    driver: webdriver.Remote
    action: webdriver.ActionChains
    defaulTab: str
    tabs = {}

    def __init__(self):
        self.driverUtil = DriverUtil()
        self.driver = self.driverUtil.driver
        self.defaulTab = self.driver.current_window_handle


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.exit()

    def exit(self):
        print('Exiting SeleniumUtil, close driver...')
        try:
            self.driver.quit()
        except Exception:
            print(f'Error closing driver')
            print(red(traceback.format_exc()))

    def tabClose(self, name: Optional[str] = None):
        try:
            self.driver.close()
            if name:
                self.tabs.pop(name)
        except Exception as ex:
            print(f'Error closing tab: {ex}')


    def tab(self, name: Optional[str] = None):
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

    def sendKeys(self, cssSel: str, value: str, keyByKeyTime: None | tuple[float, float] = None, clear=True):
        self.waitAndClick(cssSel)
        elm = self.getElm(cssSel)
        self.moveToElement(elm)
        if clear:
            if not self.clearInputbox(cssSel):
                return False
        if keyByKeyTime:
            # support both (min, max) or a single-value tuple (min == max)
            if len(keyByKeyTime) == 1:
                min_t, max_t = keyByKeyTime[0], keyByKeyTime[0]
            else:
                min_t, max_t = keyByKeyTime[0], keyByKeyTime[1]
            for c in value:
                elm.send_keys(c)
                sleep(min_t, max_t)
        else:
            elm.send_keys(value)
        sleep(0.3, 0.5)
        return elm.text == value or elm.get_attribute('value') == value


    def clearInputbox(self, cssSel: str | WebElement) -> bool:
        elm = self.getElmFromOpSelector(cssSel)
        elm.clear() # doesn't work in infojobs
        sleep(0.3, 0.5)
        if len(elm.text) > 0:
            elm.send_keys((Keys.COMMAND if isMacOS() else Keys.CONTROL) + "a")
            elm.send_keys(Keys.BACKSPACE)
            sleep(0.3, 0.5)
        return len(elm.text)==0
        
    def checkboxUnselect(self, cssSel: str):
        checkbox = self.getElm(cssSel)
        self.moveToElement(checkbox)
        if checkbox.is_selected():
            self.driver.execute_script("arguments[0].click();", checkbox)

    def waitUntilPageIsLoaded(self, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until(
            lambda driver: driver.execute_script('return document.readyState;') == 'complete')

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
            print(yellow(f'{msg}: {type(ex).__name__}'))
            if showException:
                print(red(traceback.format_exc()))
            return False

    def scrollIntoView_noError(self, cssSel: str | WebElement):
        try:
            self.scrollIntoView(cssSel)
            return True
        except Exception:
            print(yellow(f'scrollIntoView_noError, {cssSel} not Found'), end='')
            return False

    def moveToElement(self, elm: str | WebElement):
        webdriver.ActionChains(self.driver).move_to_element(self.getElmFromOpSelector(elm)).perform()

    def getHtml(self, cssSel: str) -> str:
        if value:= self.getAttr(cssSel, 'innerHTML'):
            return value
        raise Exception(f'Could not get innerHTML from {cssSel}')

    def getText(self, cssSel: str | WebElement) -> str:
        return self.getElm(cssSel).text

    def getAttr(self, cssSel: str | WebElement, attr: str) -> str:
        if value:=self.getElm(cssSel).get_attribute(attr):
            return value 
        raise Exception(f'Could not get attribute {attr} from {cssSel}')

    def getAttrOf(self, elm: WebElement, cssSel: str, attr: str) -> str | None:
        return self.getElmOf(elm, cssSel).get_attribute(attr)
    
    def setAttr(self, elm: str | WebElement, attr: str, value: str):
        elmObj = self.getElmFromOpSelector(elm)
        self.driver.execute_script(f"arguments[0].setAttribute('{attr}', '{value}')", elmObj)

    def back(self):
        self.driver.back()


def sleep(ini: float, end: float, disable=False):
    if disable:
        return
    time.sleep(random.uniform(ini, end))
