import os
import traceback

def getProjectTraceItems(e: Exception) -> str:
    return ' -- '.join([f'{os.path.basename(x.filename)}:{x.lineno}' for x in traceback.extract_tb(e.__traceback__) if 'site-packages' not in x.filename])
