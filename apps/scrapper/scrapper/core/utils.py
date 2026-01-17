import traceback
from typing import Optional
from commonlib.terminalColor import red, yellow

def debug(debugFlag: bool, msg: str = '', exception: Optional[bool]=None):
    exception = exception if exception is not None else debugFlag
    if debugFlag:
        msg = f" (debug active) {msg}, press a key"
        if exception:
            print(yellow(msg))
            input(red(traceback.format_exc()))
        else:
            input(red(msg))
    else:
        if exception:
            print(yellow(msg))
            print(red(traceback.format_exc()))
        else:
            print(red(msg))

def pageExists(page: int, totalResults: int, jobsXPage: int) -> bool:
    import math
    return page > 1 and totalResults > 0 and page < math.ceil(totalResults / jobsXPage)
