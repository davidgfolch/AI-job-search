import re
from typing import Any, Optional, Tuple

from commonlib.terminalColor import red

ERROR_PREFIX = 'MysqlError: '

def getAndFilter(pills, value):
    if not pills:
        return ''
    fields = list(map(lambda f: f'{f}', pills))
    if len(fields) > 0:
        if not value:
            filters = ' or '.join(fields)
            return f' and not ({filters})'
        else:
            filters = ' and '.join(fields)
            return f' and ({filters})'
    return ''


def formatSql(query, formatAndsOrs=True):
    return regexSubs(query, [
        (r',(?!= )', r', '),
        (r'(?!=and)(?!=or) (and|or) ', r'\n\t \1 ') if formatAndsOrs else None,
        (r'\n+', r'\n')
    ])


def regexSubs(txt: str, regExs: list[(re.Pattern, re.Pattern)]):
    res = txt
    for r in regExs:
        if r:
            res = re.sub(r[0], r[1], res)
    return res


# static methods
def getColumnTranslated(c):
    return re.sub(r'`', '', re.sub(r'[_-]', ' ', c)).capitalize()


def updateFieldsQuery(ids: list, fieldsValues: dict) -> Tuple[Optional[str], Optional[dict]]:
    if len(ids) < 1:
        return (None,None)
    query = 'UPDATE jobs SET '
    for field in fieldsValues.keys():
        query += f'{field}=%({field})s,'

    query = query[:len(query)-1] + '\n'
    query += 'WHERE id ' + inFilter(ids)
    return query, fieldsValues


def deleteJobsQuery(ids: list[str]):
    if len(ids) < 1:
        return
    query = 'DELETE FROM jobs '
    query += 'WHERE id ' + inFilter(ids)
    return query


def error(ex, suffix='', end='\n'):
    print(red(f'{ERROR_PREFIX}{ex}{suffix}'), end=end, flush=True)


def emptyToNone(params: tuple[Any]):
    return tuple(
        map(lambda p:
            None if isinstance(p, str) and p.strip() == '' else p,
            params))


def maxLen(params: tuple[Any], maxLens: tuple[int]):
    def mapParam(p: tuple):
        val = p[0]
        max = p[1]
        if max is not None and isinstance(val, str) and len(val) > max:
            return val[:(max-len('[...]'))]+'[...]'
        return val
    return tuple(
        map(lambda p: mapParam(p), zip(params, maxLens, strict=False)))


def inFilter(ids: list[int]):
    idsFilter = ','.join([str(id) for id in ids])
    return f' in ({idsFilter})'


def binaryColumnIgnoreCase(col: str) -> str:
    if col in ['comments', 'markdown']:
        return f'CONVERT({col} USING utf8mb4) COLLATE utf8mb4_0900_ai_ci'
    return col


def scapeRegexChars(txt: str) -> str:
    """Escape regex special characters for use in SQL RLIKE queries"""
    scaped = re.escape('[()]|*+')
    val = re.sub(f'[{scaped}]', '', txt)
    return val


def avoidInjection(value: str, param_name: str = "parameter") -> str:
    """
    Validate that a string doesn't contain potentially dangerous SQL patterns.
    
    Args:
        value: The string to validate
        param_name: Name of the parameter for error messages
        
    Returns:
        The validated string
        
    Raises:
        ValueError: If dangerous SQL patterns are detected
    """
    if not value or not isinstance(value, str):
        raise ValueError(f"{param_name} must be a non-empty string")
    # Check for common SQL injection patterns
    dangerous_patterns = [
        (r';', 'semicolon'),
        (r'--', 'SQL comment'),
        (r'/\*', 'multi-line comment start'),
        (r'\*/', 'multi-line comment end'),
        (r'\bunion\b', 'UNION keyword'),
        (r'\bselect\b', 'SELECT keyword'),
        (r'\bdrop\b', 'DROP keyword'),
        (r'\binsert\b', 'INSERT keyword'),
        (r'\bdelete\b', 'DELETE keyword'),
        (r'\bupdate\b', 'UPDATE keyword'),
        (r'\bexec\b', 'EXEC keyword'),
        (r'\bexecute\b', 'EXECUTE keyword'),
        (r'\binto\b', 'INTO keyword'),
        (r'\bfrom\b', 'FROM keyword'),
        (r'\bwhere\b', 'WHERE keyword'),
        (r'\bor\b', 'OR keyword'),
        (r'\band\b', 'AND keyword'),
        (r'=', 'equals sign'),
        (r'<', 'less than sign'),
        (r'>', 'greater than sign'),
    ]
    value_lower = value.lower()
    for pattern, description in dangerous_patterns:
        if re.search(pattern, value_lower, re.IGNORECASE):
            raise ValueError(f"{param_name} contains potentially dangerous pattern: {description}")
    return value
