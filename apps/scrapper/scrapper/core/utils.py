import math
import traceback
import time
import random
from typing import Optional
from commonlib.observability import get_logger
from commonlib.terminalColor import red, yellow

logger = get_logger("scrapper.utils")

def sleep(ini: float, end: float, disable=False):
    if disable:
        return
    time.sleep(random.uniform(ini, end))

def debug(debugFlag: bool, msg: str = '', exception: Optional[bool]=None):
    exception = exception if exception is not None else debugFlag
    if debugFlag:
        msg = f" (debug active) {msg}, press a key"
        if exception:
            logger.warning("debug.pause_requested", message=msg, traceback_available=True, console=yellow(msg))
            exc_str = traceback.format_exc()
            if exc_str and "NoneType: None" not in exc_str:
                input(red(exc_str))
            else:
                input(red("No traceback available."))
        else:
            input(red(msg))
    else:
        if exception:
            logger.exception("debug.interrupted", message=msg, console=yellow(msg) + "\n" + red(traceback.format_exc()))
        else:
            logger.error("debug.message", message=msg, console=red(msg))

def pageExists(page: int, totalResults: int, jobsXPage: int) -> bool:
    return page > 1 and totalResults > 0 and page <= math.ceil(totalResults / jobsXPage)

def abortExecution() -> bool:
    logger.warning("scraper.interrupted", wait_seconds=3, hint="Press Ctrl+C to stop all scrappers",
                    console=yellow("Scraper interrupted. Waiting 3 seconds... (Ctrl+C to stop all)"))
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        logger.warning("scraper.stopping", console=red("Stopping all scrappers..."))
        return True
    return False

def runPreload(properties: dict) -> bool:
    """Check if preload is needed based on properties."""
    return not properties.get('preloaded', False)
