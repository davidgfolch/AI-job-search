import traceback
import time
import random
from typing import Optional
from commonlib.terminalColor import red, yellow, cyan

def sleep(ini: float, end: float, disable=False):
    if disable:
        return
    time.sleep(random.uniform(ini, end))

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

def abortExecution() -> bool:
    print(yellow("Scraper interrupted. Waiting 3 seconds... (Ctrl+C to stop all)"))
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        print(red("Stopping all scrappers..."))
        return True
    return False

def runPreload(properties: dict, close_tab_key: str = 'CLOSE_TAB', run_in_tabs: bool = True) -> bool:
    """Check if preload is needed based on properties."""
    return not properties.get('preloaded', False) or properties.get(close_tab_key, False) or not run_in_tabs
