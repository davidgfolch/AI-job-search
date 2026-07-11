from commonlib.decorator.retry import retry
from commonlib.terminalColor import yellow, green
from ...services.selenium.browser_service import sleep
from ...services.gmail.glassdoor_gmail_service import GlassdoorGmailService
from ...core import baseScrapper

# Indeed auth button on Glassdoor
CSS_SEL_INDEED_AUTH_BUTTON = '[data-test="unified-auth-indeed-button"]'

# Popup login form
CSS_SEL_EMAIL_INPUT = 'input[name="__email"]'
CSS_SEL_EMAIL_SUBMIT = 'button[data-tn-element="auth-page-email-submit-button"]'

# OTP flow
CSS_SEL_GOOGLE_OTP_FALLBACK = "#auth-page-google-otp-fallback"
CSS_SEL_PASSCODE_INPUT = "#passcode-input"
CSS_SEL_OTP_VERIFY_SUBMIT = 'button[data-tn-element="otp-verify-login-submit-button"]'
CSS_SEL_PASSCODE_ERROR = "#label-passcode-input-error"


class GlassdoorAuthenticator:
    def __init__(self, selenium):
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
        sleep(3, 3)
        print("Filling email in popup...")
        self.selenium.sendKeys(CSS_SEL_EMAIL_INPUT, self.USER_EMAIL)
        sleep(1, 2)
        self.selenium.waitAndClick(CSS_SEL_EMAIL_SUBMIT)
        self.selenium.waitUntilPageIsLoaded()
        sleep(2, 3)
        print("Clicking OTP fallback link...")
        self.selenium.waitAndClick(CSS_SEL_GOOGLE_OTP_FALLBACK)
        self.selenium.waitUntilPageIsLoaded()
        sleep(2, 3)
        print("Retrieving 2FA code from email...")
        self._get_otp_code()
        print("Closing popup window...")
        self.selenium.close_and_switch_back(self._popup_handle)
        self._popup_handle = None

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
        inputError = self.selenium.getElms(CSS_SEL_PASSCODE_ERROR)
        if len(inputError) > 0 and inputError[0].is_displayed():
            print("OTP code validation failed (error element displayed)")
            raise ValueError("Invalid OTP code")
        print("OTP code accepted")
