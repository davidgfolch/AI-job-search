from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
from commonlib.decorator.retry import StackTrace, retry
from commonlib.observability import get_logger
from ...services.selenium.browser_service import sleep

logger = get_logger("scrapper.captchaHandler")

CSS_SEL_CAPTCHA_CHALLENGE = 'iframe[src*="recaptcha"], iframe[src*="hcaptcha"], .cf-turnstile, #captcha-box, [data-callback]'

@retry(retries=60, delay=1, raiseException=False, stackTrace=StackTrace.NEVER)
def _detect_captcha(selenium, cssSelector):
    if selenium.waitUntil_presenceLocatedElement_noError(cssSelector):
        return
    logger.warning("captcha.detected", selector=cssSelector, action="solve_manually_in_browser")
    raise Exception("Could not login because cloudFlare security filter was not resolved")
