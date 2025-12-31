import random
import time
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from scrapper.core import baseScrapper
from scrapper.services.selenium.seleniumSocketConnRetry import seleniumSocketConnRetry
from commonlib.terminalColor import yellow
from commonlib.util import isMacOS

SCROLL_INTO_VIEW_SCRIPT = "arguments[0].scrollIntoView({ block: 'end',  behavior: 'smooth' });"

def sleep(ini: float, end: float, disable=False):
    if disable:
        return
    time.sleep(random.uniform(ini, end))

class ElementService:
    def __init__(self, driver: webdriver.Remote):
        self.driver = driver

    @seleniumSocketConnRetry()
    def getElm(self, cssSel: str | WebElement):
        if isinstance(cssSel, WebElement):
            return cssSel
        return self.driver.find_element(By.CSS_SELECTOR, cssSel)

    @seleniumSocketConnRetry()
    def getElmOf(self, elm: WebElement, cssSel: str):
        return elm.find_element(By.CSS_SELECTOR, cssSel)

    @seleniumSocketConnRetry()
    def getElms(self, cssSel: str, driverOverride=None) -> List[WebElement]:
        if driverOverride:
            return driverOverride.find_elements(By.CSS_SELECTOR, cssSel)
        return self.driver.find_elements(By.CSS_SELECTOR, cssSel)

    @seleniumSocketConnRetry()
    def sendKeys(self, cssSel: str, value: str, keyByKeyTime: None | tuple[float, float] = None, clear=True):
        self.waitAndClick(cssSel)
        elm = self.getElm(cssSel)
        self.moveToElement(elm)
        if clear:
            if not self.clearInputbox(cssSel):
                return False
        if keyByKeyTime:
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

    @seleniumSocketConnRetry()
    def clearInputbox(self, cssSel: str | WebElement) -> bool:
        elm = self.getElmFromOpSelector(cssSel)
        elm.clear() 
        sleep(0.3, 0.5)
        if len(elm.text) > 0:
            elm.send_keys((Keys.COMMAND if isMacOS() else Keys.CONTROL) + "a")
            elm.send_keys(Keys.BACKSPACE)
            sleep(0.3, 0.5)
        return len(elm.text)==0
        
    @seleniumSocketConnRetry()
    def checkboxUnselect(self, cssSel: str):
        checkbox = self.getElm(cssSel)
        self.moveToElement(checkbox)
        if checkbox.is_selected():
            self.driver.execute_script("arguments[0].click();", checkbox)

    @seleniumSocketConnRetry()
    def scrollIntoView(self, cssSel: str | WebElement):
        elm = self.getElmFromOpSelector(cssSel)
        self.driver.execute_script(SCROLL_INTO_VIEW_SCRIPT, elm)
        self.waitUntilVisible(elm)
        self.moveToElement(elm)
    
    @seleniumSocketConnRetry()
    def waitUntilClickable(self, cssSel: str | WebElement, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable, self.getElmFromOpSelector(cssSel))

    @seleniumSocketConnRetry()
    def waitUntilVisible(self, cssSel: str | WebElement, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until(EC.visibility_of, self.getElmFromOpSelector(cssSel))

    @seleniumSocketConnRetry()
    def waitUntil_presenceLocatedElement(self, cssSel: str | WebElement, timeout: int = 10):
        WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located, self.getElmFromOpSelector(cssSel))

    @seleniumSocketConnRetry()
    def waitAndClick(self, cssSel: str | WebElement, timeout: int = 10, scrollIntoView: bool = False):
        if scrollIntoView:
            self.scrollIntoView(cssSel)
        self.waitUntilClickable(cssSel, timeout)
        elm = self.getElmFromOpSelector(cssSel)
        self.moveToElement(elm)
        elm.click()

    @seleniumSocketConnRetry()
    def getElmFromOpSelector(self, cssSel: str | WebElement) -> WebElement:
        return self.getElm(cssSel) if isinstance(cssSel, str) else cssSel

    @seleniumSocketConnRetry()
    def waitAndClick_noError(self, cssSel: str, msg: str, showException=True) -> bool:
        try:
            self.waitAndClick(cssSel)
            return True
        except Exception:
            print(yellow(f'{msg}'))
            if showException:
                baseScrapper.debug(debugFlag=False, exception=True)
            return False

    @seleniumSocketConnRetry()
    def scrollIntoView_noError(self, cssSel: str | WebElement):
        try:
            self.scrollIntoView(cssSel)
            return True
        except Exception:
            print(yellow(f'scrollIntoView_noError, {cssSel} not Found'), end='')
            return False

    @seleniumSocketConnRetry()
    def moveToElement(self, elm: str | WebElement):
        webdriver.ActionChains(self.driver).move_to_element(self.getElmFromOpSelector(elm)).perform()

    @seleniumSocketConnRetry()
    def getHtml(self, cssSel: str) -> str:
        if value:= self.getAttr(cssSel, 'innerHTML'):
            return value
        raise Exception(f'Could not get innerHTML from {cssSel}')

    @seleniumSocketConnRetry()
    def getText(self, cssSel: str | WebElement) -> str:
        return self.getElm(cssSel).text

    @seleniumSocketConnRetry()
    def getAttr(self, cssSel: str | WebElement, attr: str) -> str:
        if value:=self.getElm(cssSel).get_attribute(attr):
            return value 
        raise Exception(f'Could not get attribute {attr} from {cssSel}')

    @seleniumSocketConnRetry()
    def getAttrOf(self, elm: WebElement, cssSel: str, attr: str) -> str | None:
        return self.getElmOf(elm, cssSel).get_attribute(attr)
    
    @seleniumSocketConnRetry()
    def setAttr(self, elm: str | WebElement, attr: str, value: str):
        elmObj = self.getElmFromOpSelector(elm)
        self.driver.execute_script(f"arguments[0].setAttribute('{attr}', '{value}')", elmObj)
