from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
from commonlib.decorator.retry import StackTrace, retry
from commonlib.terminalColor import yellow
from ...services.selenium.browser_service import sleep

CSS_SEL_CAPTCHA_CHALLENGE = 'iframe[src*="recaptcha"], iframe[src*="hcaptcha"], .cf-turnstile, #captcha-box, [data-callback]'

@retry(retries=60, delay=1, raiseException=False, stackTrace=StackTrace.NEVER)
def _detect_captcha(selenium, cssSelector):
    if selenium.waitUntil_presenceLocatedElement_noError(cssSelector):
        return
    print(yellow("Captcha challenge detected! Please solve it manually in the browser..."))
    raise Exception("Could not login because cloudFlare security filter was not resolved")
