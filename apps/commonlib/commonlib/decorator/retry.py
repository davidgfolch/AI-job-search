from enum import Enum
from functools import wraps
import traceback
from typing import Callable, Any
from time import sleep

from ..exceptionUtil import getProjectTraceItems
from ..terminalColor import red, yellow


class StackTrace(Enum):
    ALWAYS = 1
    LAST_RETRY = 2
    NEVER = 3


def retry(retries: int = 5,
          delay: float = 2,
          exception: type[Exception] = Exception,
          stackTrace: StackTrace = StackTrace.LAST_RETRY,
          exceptionFnc: Callable = (lambda: None),
          raiseException: bool = True) -> Callable:
    """
    Attempt to call a function, if it fails, try again with a specified delay.

    - retries: The max amount of retries you want for the function call
    - delay: The delay (in seconds) between each function retry
    - stackTrace: Show stackTrace if error raises
    - exceptionFnc: function to execute if exception occurs
    - raiseException: if not raiseException just returns false on exception
    """
    if retries < 1 or delay <= 0:
        raise ValueError('@retry retries should be >= 1 and delay > 0')

    def decorator(fnc: Callable):
        @wraps(fnc)
        def wrapper(*args, **kwargs) -> Any:
            for i in range(1, retries + 2):
                try:
                    return fnc(*args, **kwargs)
                except KeyboardInterrupt as e:
                    raise e
                except exception as e:
                    if i == retries + 1:
                        if raiseException:
                            raise e
                        if stackTrace != StackTrace.NEVER:
                            print(red(traceback.format_exc()), flush=True)
                        else:
                            print(red(str(e)), flush=True)
                        return False
                    print(yellow(f'{e.__class__.__name__} calling function {fnc.__name__}()'), end='', flush=True)
                    if i > retries - 1 and stackTrace != StackTrace.NEVER:
                        trace = getProjectTraceItems(e)
                        print(f' -- {trace} -> ', end='', flush=True)
                    print(yellow(f' Retry {i}/{retries}... '), end='', flush=True)
                    if stackTrace == StackTrace.ALWAYS:
                        print(red(traceback.format_exc()), flush=True)
                    if exceptionFnc is not None:
                        try:
                            exceptionFnc(*args, **kwargs)
                        except TypeError:
                            exceptionFnc()
                    sleep(delay)

        return wrapper

    return decorator
