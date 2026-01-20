from typing import List, Optional
from scrapper.core.utils import debug
from scrapper.services.selenium.driverUtil import DriverUtil
from scrapper.services.selenium.seleniumSocketConnRetry import seleniumSocketConnRetry
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement

from scrapper.services.selenium.browser_service import BrowserService
from scrapper.services.selenium.element_service import ElementService

class SeleniumService:

    driverUtil: DriverUtil
    driver: webdriver.Remote
    browser_service: BrowserService
    element_service: ElementService

    def __init__(self, debug: bool):
        self.debug = debug
        self.driverUtil = DriverUtil()
        self.driver = self.driverUtil.driver
        self.browser_service = BrowserService(self.driver)
        self.element_service = ElementService(self.driver)

    @property
    def defaulTab(self):
        return self.browser_service.default_tab

    @property
    def tabs(self):
        return self.browser_service.tabs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.exit()

    def usesUndetectedDriver(self) -> bool:
        return self.driverUtil.useUndetected
        
    @seleniumSocketConnRetry()
    def exit(self):
        print('Exiting SeleniumUtil, close driver...')
        try:
            self.driver.quit()
            # Monkey patch quit to avoid double closing in __del__ (undetected_chromedriver issue on Windows)
            self.driver.quit = lambda: None
        except Exception:
            print(f'Error closing driver')
            debug(debugFlag=False, exception=True)

    def tabClose(self, name: Optional[str] = None):
        self.browser_service.tabClose(name)

    def tab(self, name: Optional[str] = None):
        self.browser_service.tab(name)

    def loadPage(self, url: str):
        self.browser_service.loadPage(url)

    def getUrl(self):
        return self.browser_service.getUrl()

    def waitUntilPageUrlContains(self, url: str, timeout: int = 10):
        self.browser_service.waitUntilPageUrlContains(url, timeout)

    def getElm(self, cssSel: str | WebElement):
        return self.element_service.getElm(cssSel)

    def getElmOf(self, elm: WebElement, cssSel: str):
        return self.element_service.getElmOf(elm, cssSel)

    def getElms(self, cssSel: str, driverOverride=None) -> List[WebElement]:
        return self.element_service.getElms(cssSel, driverOverride)

    def setFocus(self, cssSel: str):
        self.driver.execute_script("arguments[0].focus();", self.getElm(cssSel))

    def sendEscapeKey(self):
        self.browser_service.sendEscapeKey()

    def sendKeys(self, cssSel: str, value: str, keyByKeyTime: None | tuple[float, float] = None, clear=True):
        return self.element_service.sendKeys(cssSel, value, keyByKeyTime, clear)

    def clearInputbox(self, cssSel: str | WebElement) -> bool:
        return self.element_service.clearInputbox(cssSel)
        
    def checkboxUnselect(self, cssSel: str):
        self.element_service.checkboxUnselect(cssSel)

    def waitUntilPageIsLoaded(self, timeout: int = 10):
        self.browser_service.waitUntilPageIsLoaded(timeout)

    def scrollProgressive(self, distance: int):
        self.browser_service.scrollProgressive(distance)

    def scrollIntoView(self, cssSel: str | WebElement):
        self.element_service.scrollIntoView(cssSel)
    
    def waitUntilClickable(self, cssSel: str | WebElement, timeout: int = 10):
        self.element_service.waitUntilClickable(cssSel, timeout)

    def waitUntilVisible(self, cssSel: str | WebElement, timeout: int = 10):
        self.element_service.waitUntilVisible(cssSel, timeout)

    def waitUntil_presenceLocatedElement(self, cssSel: str | WebElement, timeout: int = 10):
        self.element_service.waitUntil_presenceLocatedElement(cssSel, timeout)

    def waitAndClick(self, cssSel: str | WebElement, timeout: int = 10, scrollIntoView: bool = False):
        self.element_service.waitAndClick(cssSel, timeout, scrollIntoView)

    def waitAndClick_noError(self, cssSel: str, msg: str, showException=True) -> bool:
        return self.element_service.waitAndClick_noError(cssSel, msg, showException)

    def scrollIntoView_noError(self, cssSel: str | WebElement):
        return self.element_service.scrollIntoView_noError(cssSel)

    def moveToElement(self, elm: str | WebElement):
        self.element_service.moveToElement(elm)

    def getHtml(self, cssSel: str) -> str:
        return self.element_service.getHtml(cssSel)

    def getText(self, cssSel: str | WebElement) -> str:
        return self.element_service.getText(cssSel)

    def getAttr(self, cssSel: str | WebElement, attr: str) -> str:
        return self.element_service.getAttr(cssSel, attr)

    def getAttrOf(self, elm: WebElement, cssSel: str, attr: str) -> str | None:
        return self.element_service.getAttrOf(elm, cssSel, attr)
    
    def setAttr(self, elm: str | WebElement, attr: str, value: str):
        self.element_service.setAttr(elm, attr, value)

    def back(self):
        self.browser_service.back()
