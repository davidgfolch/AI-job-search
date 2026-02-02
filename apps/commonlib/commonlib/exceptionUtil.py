import os
import re
import traceback
from typing import Union

def getProjectTraceItems(e: Exception) -> str:
    return ' -- '.join([f'{os.path.basename(x.filename)}:{x.lineno}' for x in traceback.extract_tb(e.__traceback__) if 'site-packages' not in x.filename])

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
