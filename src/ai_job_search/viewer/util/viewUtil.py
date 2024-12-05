import re

from ai_job_search.viewer.util.stUtil import setState


def mapDetailForm(jobData, fieldsBool):
    boolFieldsValues = []
    comments, salary, company, client = (None, None, None, None)
    if jobData:
        comments, salary, company, client = (jobData['comments'],
                                             jobData['salary'],
                                             jobData['company'],
                                             jobData['client'])
        setState('comments', comments)
        setState('salary', salary)
        setState('company', company)
        setState('client', client)
        boolMapper = map(lambda f: f if
                         jobData.get(f, False) else None,
                         fieldsBool)
        boolFieldsValues = list(filter(lambda x: x, boolMapper))
    return (boolFieldsValues, comments if comments else '',
            salary, company, client)


def regexSubs(txt: str, regExs: list[(re.Pattern, re.Pattern)]):
    res = txt
    for r in regExs:
        res = re.sub(r[0], r[1], res)
    return res


def formatSql(query):
    return regexSubs(query, [
        (r',(?!= )', r', '),
        (r'( and | or )', r'\n\t\1'),
        (r'\n+', r'\n')
    ])
