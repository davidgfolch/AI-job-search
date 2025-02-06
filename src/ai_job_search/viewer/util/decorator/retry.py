from enum import Enum
from functools import wraps
import traceback
from typing import Callable, Any
from time import sleep

from ai_job_search.tools.terminalColor import red, yellow


class ShowStackTrace(Enum):
    ALWAYS = 1
    LAST_RETRY = 2
    NEVER = 3


def retry(retries: int = 5,
          delay: float = 2,
          exception: Exception = Exception,
          stackStrace: ShowStackTrace = ShowStackTrace.LAST_RETRY,
          exceptionFnc: Callable = None,
          raiseException: bool = True) -> Callable:
    """
    Attempt to call a function, if it fails, try again with a specified delay.

    - retries: The max amount of retries you want for the function call
    - delay: The delay (in seconds) between each function retry
    - stackTrace: Show stackTrace if error raises
    - exceptionFnc: function to execute if exception occurs
    - raiseException: if not raiseException just returns false
    """
    if retries < 1 or delay <= 0:
        raise ValueError('@retry retries should be >= 1 and delay > 0')

    def decorator(fnc: Callable):
        @wraps(fnc)
        def wrapper(*args, **kwargs) -> Any:
            for i in range(1, retries + 2):
                try:
                    return fnc(*args, **kwargs)
                except exception as e:
                    if i == retries + 1:
                        if raiseException:
                            raise e
                        if stackStrace:
                            print(red(traceback.format_exc()))
                        else:
                            print(red(e))
                        return False
                    print(yellow(f'Error calling function {fnc.__name__}()',
                                 f' -> Retry {i}/{retries}...'))
                    if stackStrace:
                        print(red(traceback.format_exc()))
                    if exceptionFnc is not None:
                        exceptionFnc()
                    sleep(delay)
        return wrapper

    return decorator
