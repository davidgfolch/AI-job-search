import re
from typing import Iterator

def hasLen(iter: Iterator):
    return any(True for _ in iter)

def removeBlanks(text):
    return re.sub(r'[\n\b]+', '', text, re.M).strip()

def hasLenAnyText(*texts: str) -> list[bool]:
    return [t is not None and len(removeBlanks(t)) > 0 for t in texts]

def toBool(str_val: str) -> bool:
    if str_val is None:
        return False
    return str_val.lower() in ['true', '1', 'yes']

def removeExtraEmptyLines(txt: str) -> str:
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'\s+\n', '\n', txt))

def removeNewLines(txt: str) -> str:
    try:
        return txt.replace('\n', ' ').replace('\r', '')
    except Exception:
        return str(txt)

def join(*args) -> str:
    return ' '.join([str(arg) for arg in args if arg])
