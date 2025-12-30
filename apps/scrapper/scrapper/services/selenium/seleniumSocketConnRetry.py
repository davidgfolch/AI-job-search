


from typing import Callable

import urllib3

from commonlib.decorator.retry import retry


def seleniumSocketConnRetry() -> Callable:
    """
    Default retry configuration for SeleniumUtil socket disconnection problems
    """
    return retry(retries=20, delay=3, exception=urllib3.exceptions.ReadTimeoutError)
