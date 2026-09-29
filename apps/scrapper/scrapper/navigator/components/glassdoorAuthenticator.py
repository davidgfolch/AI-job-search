from commonlib.decorator.retry import retry
from commonlib.observability import get_logger
from ...services.selenium.seleniumService import SeleniumService
from ...services.selenium.browser_service import sleep
from ...services.gmail.glassdoor_gmail_service import GlassdoorGmailService
from ...core import baseScrapper
from .captchaHandler import _detect_captcha
from .exceptionHandler import raise_if_otp_invalid

logger = get_logger("scrapper.glassdoorAuthenticator")

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
        logger.debug("glassdoor.auth.indeed_button_click")
        old_handles = self.selenium.driver.window_handles
        self.selenium.waitAndClick(CSS_SEL_INDEED_AUTH_BUTTON)
        logger.debug("glassdoor.auth.popup_waiting")
        self._popup_handle = self.selenium.wait_for_new_window(old_handles)
        self.selenium.switch_to_window(self._popup_handle)
        self.selenium.set_window_size(1370, 1000)
        sleep(3, 3)
        logger.debug("glassdoor.auth.email_filling")
        self.selenium.sendKeys(CSS_SEL_EMAIL_INPUT, self.USER_EMAIL)
        self._accept_cookies_if_present()
        self._login_submit()
        sleep(3, 3)
        self._accept_cookies_if_present()
        _detect_captcha(self.selenium, CSS_SEL_GOOGLE_OTP_FALLBACK)
        self._fill_OTP_code()
        logger.debug("glassdoor.auth.otp_retrieving")
        self._get_otp_code()
        logger.debug("glassdoor.auth.popup_closing")
        self.selenium.close_and_switch_back(self._popup_handle)
        self._popup_handle = None

    @retry()
    def _login_submit(self):
        logger.debug("glassdoor.auth.email_submitting")
        self.selenium.waitAndClick(CSS_SEL_EMAIL_SUBMIT)
        self.selenium.waitUntilPageIsLoaded()
        sleep(2, 3)
    
    @retry()
    def _fill_OTP_code(self):
        logger.debug("glassdoor.auth.otp_fallback_click")
        self.selenium.waitAndClick(CSS_SEL_GOOGLE_OTP_FALLBACK)
        self.selenium.waitUntilPageIsLoaded()
        sleep(2, 3)
        
    def _accept_cookies_if_present(self):
        try:
            self.selenium.waitUntilVisible(CSS_SEL_COOKIE_ACCEPT, timeout=5)
            self.selenium.waitAndClick(CSS_SEL_COOKIE_ACCEPT)
            logger.debug("glassdoor.auth.cookies_accepted")
        except Exception:
            logger.debug("glassdoor.auth.no_cookie_banner")

    @retry(delay=1)
    def _get_otp_code(self):
        sleep(5, 5)
        logger.info("glassdoor.auth.gmail_connecting")
        with GlassdoorGmailService() as gmail:
            code = gmail.wait_for_glassdoor_verification_code(120)
        logger.info("glassdoor.auth.otp_received", code_length=len(code))
        self.selenium.sendKeys(CSS_SEL_PASSCODE_INPUT, code)
        self.selenium.waitAndClick(CSS_SEL_OTP_VERIFY_SUBMIT)
        self.selenium.waitUntilPageIsLoaded()
        raise_if_otp_invalid(self.selenium)
        logger.info("glassdoor.auth.otp_accepted")
