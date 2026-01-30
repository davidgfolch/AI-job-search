from commonlib.decorator.retry import retry, StackTrace
from ...services.selenium.browser_service import sleep
from ...services.gmail.indeed_gmail_service import IndeedGmailService
from ...core import baseScrapper

LOGIN_PAGE = "https://es.indeed.com/account/login"

# LOGIN
CSS_SEL_LOGIN_EMAIL = 'input[type="email"]:not([style*="display: none"]):not([style*="display:none"]), input[name="email"]:not([style*="display: none"]):not([style*="display:none"]), input[autocomplete="email"]:not([style*="display: none"]):not([style*="display:none"]), input[placeholder*="email" i]:not([style*="display: none"]):not([style*="display:none"]), #ifl-InputFormField-3:not([style*="display: none"]):not([style*="display:none"]), .email-input, [data-testid="email-input"]'
CSS_SEL_LOGIN_PASSWORD = 'input[type="password"]:not([style*="display: none"]):not([style*="display:none"]), input[name="password"]:not([style*="display: none"]):not([style*="display:none"]), input[autocomplete="current-password"]:not([style*="display: none"]):not([style*="display:none"]), #ifl-InputFormField-6:not([style*="display: none"]):not([style*="display:none"]), .password-input, [data-testid="password-input"]'
CSS_SEL_LOGIN_SUBMIT = 'button[type="submit"], button[data-testid="submit"], button[data-tn="submit"]'
CSS_SEL_2FA_INPUT = 'input[name="code"], input[type="text"][placeholder*="code"]'
CSS_SEL_2FA_SUBMIT = 'button[type="submit"]'
CSS_SEL_GOOGLE_OTP_FALLBACK = "#auth-page-google-otp-fallback"
CSS_SEL_2FA_PASSCODE_INPUT = "#passcode-input"
CSS_SEL_2FA_VERIFY_SUBMIT = 'button[data-tn-element="otp-verify-login-submit-button"]'
CSS_SEL_WEBAUTHN_CONTINUE = "#pass-WebAuthn-continue-button"

# COOKIE CONSENT
CSS_SEL_COOKIE_ACCEPT = "#onetrust-accept-btn-handler, button[data-testid='accept-all'], .accept-cookies, [aria-label*='Accept' i]"

class IndeedAuthenticator:
    def __init__(self, selenium):
        self.selenium = selenium
        # Get Indeed credentials from environment
        self.USER_EMAIL, self.USER_PWD, _ = baseScrapper.getAndCheckEnvVars("INDEED")

    def accept_cookies(self):
        self.selenium.waitAndClick_noError(CSS_SEL_COOKIE_ACCEPT, "Could not accept cookies")

    @retry(retries=60, delay=1, raiseException=False, stackTrace=StackTrace.NEVER)
    def waitForCloudflareFilterInLogin(self):
        if self.selenium.waitUntil_presenceLocatedElement_noError(CSS_SEL_LOGIN_EMAIL) or \
            self.selenium.waitUntil_presenceLocatedElement_noError('#AccountMenu'):
            return True
        return False

    def login(self):
        print("Navigating to Indeed login page...")
        self.selenium.loadPage(LOGIN_PAGE)
        self.selenium.waitUntilPageIsLoaded()
        sleep(3, 3)
        if not self.waitForCloudflareFilterInLogin():
            raise Exception("Could not login because cloudFlare security filter was not resolved")
        
        # If we are already logged in (AccountMenu found), we can check and return
        if self.selenium.waitUntil_presenceLocatedElement_noError('#AccountMenu'):
            return

        print("Filling login form...")
        self.selenium.sendKeys(CSS_SEL_LOGIN_EMAIL, self.USER_EMAIL)
        self.accept_cookies()
        print("Submitting login form...")
        self.selenium.waitAndClick(CSS_SEL_LOGIN_SUBMIT)
        print("Waiting for Cloudflare filter...")
        sleep(5, 5)
        if not self.selenium.waitAndClick_noError(CSS_SEL_LOGIN_SUBMIT,
            "Could not resubmit login form after cloudflare filter...",
            showException=False):
            sleep(3, 3)
        print("Handling Google OTP fallback...")
        self.click_google_otp_fallback()
        print("Get email 2FA code...")
        self.getEmail2faCode()
        print("Ignore Access key form question")
        sleep(2, 3)
        self.ignore_access_key_form()
        sleep(2, 3)

    def click_google_otp_fallback(self):
        self.selenium.waitAndClick(CSS_SEL_GOOGLE_OTP_FALLBACK)
        sleep(5, 5)

    @retry(delay=1)
    def getEmail2faCode(self):
        sleep(5, 5)
        with IndeedGmailService() as gmail:
            code = gmail.wait_for_verification_code("login@indeed.com", 60)
        self.selenium.sendKeys(CSS_SEL_2FA_PASSCODE_INPUT, code)
        self.selenium.waitAndClick(CSS_SEL_2FA_VERIFY_SUBMIT)
        self.selenium.waitUntilPageIsLoaded()
        inputError = self.selenium.getElms("#label-passcode-input-error")
        if len(inputError) > 0 and inputError[0].is_displayed(): # invalid code, try again
            raise ValueError("Invalid code")

    def ignore_access_key_form(self):
        self.selenium.waitUntil_presenceLocatedElement(CSS_SEL_WEBAUTHN_CONTINUE)
        self.selenium.waitAndClick(CSS_SEL_WEBAUTHN_CONTINUE)
        self.selenium.waitUntilPageIsLoaded()
