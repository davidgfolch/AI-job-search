from selenium.common.exceptions import NoSuchElementException, TimeoutException
from commonlib.decorator.retry import retry, StackTrace
from ...services.selenium.browser_service import sleep

CSS_SEL_PASSCODE_ERROR = "#label-passcode-input-error"


@retry(retries=60, delay=1, raiseException=False, stackTrace=StackTrace.NEVER)
def wait_for_cloudflare_filter(selenium, email_css_selector):
    if selenium.waitUntil_presenceLocatedElement_noError(email_css_selector) or \
        selenium.waitUntil_presenceLocatedElement_noError('#AccountMenu'):
        return
    raise Exception("Could not login because cloudFlare security filter was not resolved")


def check_for_otp_error(selenium, error_css_selector=CSS_SEL_PASSCODE_ERROR):
    inputError = selenium.getElms(error_css_selector)
    if len(inputError) > 0 and inputError[0].is_displayed():
        return True
    return False


def raise_if_otp_invalid(selenium, error_css_selector=CSS_SEL_PASSCODE_ERROR, error_message="Invalid OTP code"):
    if check_for_otp_error(selenium, error_css_selector):
        raise ValueError(error_message)


def wait_for_element_present(selenium, css_selector, timeout=10):
    return selenium.waitUntil_presenceLocatedElement_noError(css_selector, timeout=timeout)


def is_element_present(selenium, css_selector):
    return selenium.waitUntil_presenceLocatedElement_noError(css_selector, timeout=3)
