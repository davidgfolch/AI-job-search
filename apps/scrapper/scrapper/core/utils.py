import math
import time
import random

from commonlib.debug_utils import debug
from commonlib.observability import get_logger
from commonlib.terminalColor import red, yellow

logger = get_logger("scrapper.utils")

__all__ = ["debug", "sleep", "pageExists", "abortExecution", "runPreload"]


def sleep(ini: float, end: float, disable=False):
    if disable:
        return
    time.sleep(random.uniform(ini, end))

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
