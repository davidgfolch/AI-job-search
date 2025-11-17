import random
import time
import os
import traceback
import undetected_chromedriver as uc
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from commonlib.decorator.retry import retry
from commonlib.terminalColor import red, yellow
from commonlib.util import getEnvBool, isMacOS

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
    useUndetected: bool


    def __init__(self):
        useUndetected = getEnvBool('USE_UNDETECTED_CHROMEDRIVER', False)
        self.useUndetected = useUndetected
        print(f'seleniumUtil init (undetected={useUndetected})')
        if useUndetected:
            chromePath = self._findChrome()
            if chromePath is not None:
                self.driver = uc.Chrome(browser_executable_path=chromePath) if chromePath else uc.Chrome()
                # # Enhanced undetected-chromedriver configuration
                # # Note: undetected_chromedriver handles most anti-detection internally
                # options = uc.ChromeOptions()
                # # Only add safe arguments that undetected-chromedriver supports
                # options.add_argument('--window-size=1920,1080')
                # options.add_argument('--disable-dev-shm-usage')
                # options.add_argument('--no-sandbox')
                # # Random user agent
                # user_agent = random.choice(DESKTOP_USER_AGENTS)
                # options.add_argument(f'--user-agent={user_agent}')

                # self.driver = uc.Chrome(
                #     browser_executable_path=chromePath if chromePath else None,
                #     options=options,
                #     version_main=None,  # Auto-detect Chrome version
                #     use_subprocess=True,
                #     headless=False  # Headless mode increases detection
                # )
                # self.driver.set_page_load_timeout(180)
                # self.driver.set_script_timeout(180)

                # # Additional stealth techniques
                # self._apply_stealth_scripts()
            else:
                print(yellow('WARNING: undetected-chromedriver requires Chrome installed. Falling back to standard Selenium.'))
                useUndetected = False
        if not useUndetected:
            opts = webdriver.ChromeOptions()
            opts.add_argument("--window-size=1920,900")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_experimental_option("excludeSwitches", ["enable-automation"])
            opts.add_experimental_option("useAutomationExtension", False)
            # Use random user agent
            user_agent = random.choice(DESKTOP_USER_AGENTS)
            opts.add_argument(f"--user-agent={user_agent}")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-gpu")
            self.driver = webdriver.Chrome(options=opts)
            self.driver.set_page_load_timeout(180)
            self.driver.set_script_timeout(180)
            self._apply_stealth_scripts()
        print(f'seleniumUtil init driver={self.driver}')
        self.defaulTab = self.driver.current_window_handle

    def _apply_stealth_scripts(self):
        """Apply advanced stealth techniques to bypass bot detection"""
        stealth_js = """
        // Overwrite the `languages` property to use a custom getter
        Object.defineProperty(navigator, 'languages', {
            get: function() { return ['en-US', 'en']; }
        });

        // Overwrite the `plugins` property to use a custom getter
        Object.defineProperty(navigator, 'plugins', {
            get: function() { return [1, 2, 3, 4, 5]; }
        });

        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // Mock chrome runtime
        window.chrome = {
            runtime: {}
        };

        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );

        // Add vendor and renderer info
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.call(this, parameter);
        };

        // Mock automation flags
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: () => 1
        });

        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });

        // Add connection info
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                rtt: 50,
                downlink: 10,
                saveData: false
            })
        });
        """
        try:
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': stealth_js
            })
        except Exception:
            # Fallback for non-CDP browsers
            try:
                self.driver.execute_script(stealth_js)
            except Exception:
                pass

    def _findChrome(self):
        import platform
        system = platform.system()
        if system == 'Windows':
            paths = [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'),
                os.path.expandvars(r'%PROGRAMFILES%\Google\Chrome\Application\chrome.exe'),
                os.path.expandvars(r'%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe'),
            ]
        else:
            paths = [
                '/usr/bin/google-chrome',
                '/usr/local/bin/google-chrome',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
            ]
        for path in paths:
            if os.path.exists(path):
                return path
        return None

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
        except Exception:
            print(f'Error closing driver')
            print(red(traceback.format_exc()))

    def isDriverAlive(self) -> bool:
        try:
            self.driver.current_url
            return True
        except Exception:
            return False

    def keepAlive(self):
        try:
            self.driver.execute_script("return 1")
        except Exception:
            pass

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
            lambda driver: driver.execute_script(
                'return document.readyState;') == 'complete')

    def scrollToBottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

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
