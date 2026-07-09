import os
import tempfile
import random
import subprocess
import re
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from commonlib.terminalColor import yellow
from commonlib.environmentUtil import getEnvBool
from commonlib.systemUtil import isWindowsOS
from .stealthScripts import STEALTH_SCRIPTS_JS

# Rotating User-Agents to avoid Cloudflare security filter
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

class DriverUtil:
    useUndetected: bool
    driver: webdriver.Chrome | webdriver.Firefox

    def __init__(self, browser: str = 'chrome'):
        self.browser = browser
        print(f'seleniumUtil init (browser={self.browser})')
        if self.browser == 'firefox':
            self._init_firefox()
        else:
            self._init_chrome()
        print(f'seleniumUtil init driver={self.driver}')

    def _init_chrome(self):
        self.useUndetected = getEnvBool('SCRAPPER_USE_UNDETECTED_CHROMEDRIVER', False)
        print(f'seleniumUtil init (undetected={self.useUndetected})')
        if self.useUndetected:
            chromePath = self._findChrome()
            if chromePath is not None:
                version_main = self._getChromeVersion(chromePath)
                print(f'Detected Chrome version: {version_main}')
                if isWindowsOS():
                    opts = uc.ChromeOptions()
                    opts.add_argument('--disable-gpu')
                    opts.add_argument('--no-sandbox')
                    opts.add_argument('--disable-dev-shm-usage')
                    temp_user_data_dir = tempfile.mkdtemp()
                    opts.add_argument(f'--user-data-dir={temp_user_data_dir}')
                    self.driver = uc.Chrome(browser_executable_path=chromePath, chrome_options=opts, version_main=version_main)
                    self._set_window_size_and_position()
                else:
                    opts = uc.ChromeOptions()
                    opts.add_argument('--disable-gpu')
                    opts.add_argument('--no-sandbox')
                    opts.add_argument('--disable-dev-shm-usage')
                    opts.add_argument('--disable-blink-features=AutomationControlled')
                    opts.add_argument('--disable-notifications')
                    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
                    self.driver = uc.Chrome(browser_executable_path=chromePath, chrome_options=opts, version_main=version_main)
                    self._set_window_size_and_position()
            else:
                print(yellow('WARNING: undetected-chromedriver requires Chrome installed. Falling back to standard Selenium.'))
                self.useUndetected = False
        if not self.useUndetected:
            opts = webdriver.ChromeOptions()
            opts.add_argument("--disable-blink-features=AutomationControlled")
            opts.add_experimental_option("excludeSwitches", ["enable-automation"])
            opts.add_experimental_option("useAutomationExtension", False)
            user_agent = random.choice(DESKTOP_USER_AGENTS)
            opts.add_argument(f"--user-agent={user_agent}")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-gpu")
            self.driver = webdriver.Chrome(options=opts)
            self._set_window_size_and_position()
            self.driver.set_page_load_timeout(180)
            self.driver.set_script_timeout(180)
            self._apply_stealth_scripts()

    def _init_firefox(self):
        opts = FirefoxOptions()
        user_agent = random.choice(DESKTOP_USER_AGENTS)
        opts.set_preference("general.useragent.override", user_agent)
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-gpu")
        self.driver = webdriver.Firefox(options=opts)
        self._set_window_size_and_position()
        self.driver.set_page_load_timeout(180)
        self.driver.set_script_timeout(180)

    def _set_window_size_and_position(self):
        avail_width = self.driver.execute_script("return screen.availWidth;")
        avail_height = self.driver.execute_script("return screen.availHeight;")
        self.driver.set_window_size(1200, avail_height - 90)
        self.driver.set_window_position(int(avail_width - 1200), 0)

    def _findChrome(self):
        import platform
        system = platform.system()
        if system == 'Windows':
            paths = [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'),
                os.path.expandvars(r'%PROGRAMFILES%\Google\Chrome\Application\chrome.exe'),
                os.path.expandvars(r'%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe')]
        else:
            paths = [
                '/usr/bin/google-chrome',
                '/usr/local/bin/google-chrome',
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium']
        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def _getChromeVersion(self, chromePath: str) -> int:
        """
        Detects the major version of the installed Chrome browser.
        Returns 0 if detection fails.
        """
        try:
            if isWindowsOS():
                # Use PowerShell to get the version on Windows
                cmd = f'(Get-Item "{chromePath}").VersionInfo.ProductVersion'
                result = subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
                version_str = result.stdout.strip()
            else:
                # Use --version flag on Linux/Mac
                result = subprocess.run([chromePath, '--version'], capture_output=True, text=True)
                version_str = result.stdout.strip()
            # Extract the major version number
            # Typical output: "Google Chrome 120.0.6099.109" or just "120.0.6099.109"
            match = re.search(r'(\d+)\.', version_str)
            if match:
                return int(match.group(1))
        except Exception as e:
            print(yellow(f'WARNING: Failed to detect Chrome version: {e}'))
        return 0

    def _apply_stealth_scripts(self):
        try:
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': STEALTH_SCRIPTS_JS})
        except Exception:
            try:
                self.driver.execute_script(STEALTH_SCRIPTS_JS)
            except Exception:
                pass

    def isAlive(self) -> bool:
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