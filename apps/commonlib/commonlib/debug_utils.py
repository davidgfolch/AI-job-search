import traceback
from typing import Optional

from commonlib.observability import get_logger
from commonlib.terminalColor import red, yellow

logger = get_logger("commonlib.debug_utils")


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
