


from functools import wraps
from typing import Any, Callable

import urllib3

from commonlib.decorator.retry import retry


@retry(retries=20, delay=10, exception=urllib3.exceptions.ReadTimeoutError)
def seleniumSocketConnRetry() -> Callable:
    """
    Default retry configuration for SeleniumUtil socket disconnection problems
    """

    def decorator(fnc: Callable):
        @wraps(fnc)
        def wrapper(*args, **kwargs) -> Any:
            return fnc(*args, **kwargs)

        return wrapper

    return decorator
