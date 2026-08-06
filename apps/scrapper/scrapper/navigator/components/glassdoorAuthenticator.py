from commonlib.decorator.retry import retry
from ...services.selenium.seleniumService import SeleniumService
from ...services.selenium.browser_service import sleep
from ...services.gmail.glassdoor_gmail_service import GlassdoorGmailService
from ...core import baseScrapper
from .captchaHandler import _detect_captcha
from .exceptionHandler import raise_if_otp_invalid

# Indeed auth button on Glassdoor
CSS_SEL_INDEED_AUTH_BUTTON = '[data-test="unified-auth-indeed-button"]'

# Popup login form
CSS_SEL_EMAIL_INPUT = 'input[name="__email"]'
CSS_SEL_EMAIL_SUBMIT = 'button[data-tn-element="auth-page-email-submit-button"]'

# Cookie consent
CSS_SEL_COOKIE_ACCEPT = "div#onetrust-button-group #onetrust-accept-btn-handler"

# OTP flow
CSS_SEL_GOOGLE_OTP_FALLBACK = "#auth-page-google-otp-fallback"
CSS_SEL_PASSCODE_INPUT = "#passcode-input"
CSS_SEL_OTP_VERIFY_SUBMIT = 'button[data-tn-element="otp-verify-login-submit-button"]'


class GlassdoorAuthenticator:
    def __init__(self, selenium: SeleniumService):
        self.selenium = selenium
        self.USER_EMAIL, _, _ = baseScrapper.getAndCheckEnvVars("INDEED")
        self._popup_handle = None

    def login(self):
        """Handle the full Indeed OTP login flow via Glassdoor popup window."""
        print("Clicking Indeed auth button on Glassdoor...")
        old_handles = self.selenium.driver.window_handles
        self.selenium.waitAndClick(CSS_SEL_INDEED_AUTH_BUTTON)
        print("Waiting for popup window...")
        self._popup_handle = self.selenium.wait_for_new_window(old_handles)
        self.selenium.switch_to_window(self._popup_handle)
        self.selenium.set_window_size(1370, 1000)
        sleep(3, 3)
        print("Filling email in popup...")
        self.selenium.sendKeys(CSS_SEL_EMAIL_INPUT, self.USER_EMAIL)
        self._accept_cookies_if_present()
        self._login_submit()
        sleep(3, 3)
        self._accept_cookies_if_present()
        _detect_captcha(self.selenium, CSS_SEL_GOOGLE_OTP_FALLBACK)
        self._fill_OTP_code()
        print("Retrieving 2FA code from email...")
        self._get_otp_code()
        print("Closing popup window...")
        self.selenium.close_and_switch_back(self._popup_handle)
        self._popup_handle = None

    @retry()
    def _login_submit(self):
        print("Submitting email in popup...")
        self.selenium.waitAndClick(CSS_SEL_EMAIL_SUBMIT)
        self.selenium.waitUntilPageIsLoaded()
        sleep(2, 3)
    
    @retry()
    def _fill_OTP_code(self):
        print("Clicking OTP fallback link...")
        self.selenium.waitAndClick(CSS_SEL_GOOGLE_OTP_FALLBACK)
        self.selenium.waitUntilPageIsLoaded()
        sleep(2, 3)
        
    def _accept_cookies_if_present(self):
        try:
            self.selenium.waitUntilVisible(CSS_SEL_COOKIE_ACCEPT, timeout=5)
            self.selenium.waitAndClick(CSS_SEL_COOKIE_ACCEPT)
            print("Cookies accepted in popup window")
        except Exception:
            print("No cookie consent banner found in popup, continuing...")

    @retry(delay=1)
    def _get_otp_code(self):
        sleep(5, 5)
        print("Connecting to Gmail IMAP to retrieve OTP code...")
        with GlassdoorGmailService() as gmail:
            code = gmail.wait_for_glassdoor_verification_code(120)
        print(f"OTP code received: {code}, entering in passcode field...")
        self.selenium.sendKeys(CSS_SEL_PASSCODE_INPUT, code)
        self.selenium.waitAndClick(CSS_SEL_OTP_VERIFY_SUBMIT)
        self.selenium.waitUntilPageIsLoaded()
        raise_if_otp_invalid(self.selenium)
        print("OTP code accepted")
