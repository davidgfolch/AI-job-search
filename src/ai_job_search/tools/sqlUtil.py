import re


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
