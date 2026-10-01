import os
import re
import sys
import traceback
from typing import Callable, List, Union

from commonlib.observability import get_logger

logger = get_logger("commonlib.exceptionUtil")


def try_or_warn(fn: Callable, warning_msg: str, show_exception: bool = False) -> bool:
    try:
        fn()
        return True
    except Exception:
        if show_exception:
            logger.exception("op.warned", message=warning_msg)
        else:
            logger.warning("op.warned", message=warning_msg)
        return False


def getProjectTraceItems(e: Exception) -> str:
    return ' -- '.join([f'{os.path.basename(x.filename)}:{x.lineno}' for x in traceback.extract_tb(e.__traceback__) if 'site-packages' not in x.filename])


def filter_trace_by_paths(paths: List[str]) -> str:
    exc = sys.exc_info()[2]
    if exc is None:
        return ""
    filtered = [f for f in traceback.extract_tb(exc) if any(p.replace('/', '\\') in f.filename or p in f.filename for p in paths)]
    if not filtered:
        return ""
    return ''.join(traceback.format_list(filtered))

def cleanUnresolvedTrace(e: Union[Exception, str], maxLength: int = 300) -> str:
    txt = str(e)
    if not txt:
        return txt
    lines = txt.split('\n')
    cleaned = [line for line in lines if not re.search(r'0x[0-9a-fA-F]{6,}', line) and '(nil)' not in line]
    result = '\n'.join(cleaned).strip()
    if len(result) > maxLength:
        result = result[:maxLength-3] + "..."
    return result
