import os
import tempfile
import random
import undetected_chromedriver as uc
from selenium import webdriver

from commonlib.terminalColor import yellow
from commonlib.util import getEnvBool, isWindowsOS

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
    driver: webdriver.Chrome

    def __init__(self):
        self.useUndetected = getEnvBool('USE_UNDETECTED_CHROMEDRIVER', False)
        print(f'seleniumUtil init (undetected={self.useUndetected})')
        if self.useUndetected:
            chromePath = self._findChrome()
            if chromePath is not None:
                version_main = self._getChromeVersion(chromePath)
                print(f'Detected Chrome version: {version_main}')
                if isWindowsOS():
                    # Avoid NoSuchElement when windows lock  https://www.perplexity.ai/search/python-selenium-undetected-chr-46Hdkb5EQCuDEmBpHh5A8Q
                    opts = uc.ChromeOptions()
                    opts.add_argument('--disable-gpu')
                    opts.add_argument('--no-sandbox')
                    opts.add_argument('--disable-dev-shm-usage')
                    # chrome_options.add_argument('--headless')  # optional, depending on need
                    temp_user_data_dir = tempfile.mkdtemp()
                    opts.add_argument(f'--user-data-dir={temp_user_data_dir}')
                    self.driver = uc.Chrome(browser_executable_path=chromePath, chrome_options=opts, version_main=version_main)
                else:
                    self.driver = uc.Chrome(browser_executable_path=chromePath, version_main=version_main)
            else:
                print(yellow('WARNING: undetected-chromedriver requires Chrome installed. Falling back to standard Selenium.'))
                self.useUndetected = False
        if not self.useUndetected:
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
        import subprocess
        import re
        
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
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': stealth_js})
        except Exception:
            # Fallback for non-CDP browsers
            try:
                self.driver.execute_script(stealth_js)
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