from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from ai_job_search.terminalColor import yellow


driver = None


class SeleniumUtil:

    def __init__(self):
        global driver
        print('selenium driver init')
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(options=options)
        print(f'selenium driver init driver={driver}')

    def loadPage(self, url: str):
        driver.get(url)

    def waitUntilPageIs(self, url: str, timeout: int = 10):
        WebDriverWait(driver, timeout).until(lambda d: d.current_url == url)

    def getElm(self, cssSel: str):
        return driver.find_element(By.CSS_SELECTOR, cssSel)

    def getElms(self, cssSel: str, driverOverride=None) -> List[WebElement]:
        if driverOverride:
            return driverOverride.find_elements(By.CSS_SELECTOR, cssSel)
        return driver.find_elements(By.CSS_SELECTOR, cssSel)

    def sendKeys(self, cssSel: str, value: str):
        self.getElm(cssSel).send_keys(value)

    def checkboxUnselect(self, cssSel: str):
        checkbox = self.getElm(cssSel)
        if checkbox.is_selected():
            driver.execute_script("arguments[0].click();", checkbox)

    def waitUntilPageIsLoaded(self, timeout: int = 10):
        WebDriverWait(driver, timeout).until(
            lambda driver: driver.execute_script(
                'return document.readyState;') == 'complete')

    def scrollIntoView(self, cssSel: str):
        driver.execute_script("arguments[0].scrollIntoView();",
                              self.getElm(cssSel))

    def waitUntilClickable(self, cssSel: str, timeout: int = 10):
        method = EC.element_to_be_clickable
        WebDriverWait(driver, timeout).until(method, self.getElm(cssSel))

    def waitAndClick(self, cssSel: str, timeout: int = 10,
                     scrollIntoView: bool = False):
        """ scrollIntoView, waits to be clickable & click"""
        if scrollIntoView:
            self.scrollIntoView(cssSel)
        self.waitUntilClickable(cssSel, timeout)
        self.getElm(cssSel).click()

    def waitAndClick_noError(self, cssSel: str, msg: str):
        try:
            self.waitAndClick(cssSel)
        except NoSuchElementException as ex:
            print(f'{msg}, exception {ex}')

    def scrollIntoView_noError(self, cssSel: str):
        try:
            self.scrollIntoView(cssSel)
            return True
        except NoSuchElementException:
            print(yellow(f'scrollIntoView_noError, {cssSel} not Found'), end='')
            return False

    def waitUntilFoundMany(self, cssSel: str, items: int, concept: str = '',
                           timeout: int = 5, retry: int = 4):
        while True:
            try:
                WebDriverWait(driver, timeout).until(
                    lambda d: len(self.getElms(cssSel, d)) == items)
            except TimeoutException as ex:
                found = len(self.getElms(cssSel))
                print(
                    f'waitUntilFound {concept}, len after exception: {found}')
                if retry > 1:
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

    # def close(self):
    #     driver.close()
