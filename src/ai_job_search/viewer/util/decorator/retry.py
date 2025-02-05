from functools import wraps
import traceback
from typing import Callable, Any
from time import sleep

from ai_job_search.tools.terminalColor import red, yellow


def retry(retries: int = 5, delay: float = 2,
          exception: Exception = Exception,
          stackStrace: bool = True) -> Callable:
    """
    Attempt to call a function, if it fails, try again with a specified delay.

    :param retries: The max amount of retries you want for the function call
    :param delay: The delay (in seconds) between each function retry
    :param stackTrace: Show stackTrace if error raises
    :return:
    """
    if retries < 1 or delay <= 0:
        raise ValueError('@retry retries should be >= 1 and delay > 0')

    def decorator(fnc: Callable) -> Callable:
        @wraps(fnc)
        def wrapper(*args, **kwargs) -> Any:
            for i in range(1, retries + 1):
                try:
                    return fnc(*args, **kwargs)
                except exception as e:
                    if i == retries:
                        raise e
                    print(yellow(f'Error calling function {fnc.__name__}()',
                                 f' -> Retry {i}/{retries}...'))
                    if stackStrace:
                        print(red(traceback.format_exc()))
                    sleep(delay)
        return wrapper

    return decorator
