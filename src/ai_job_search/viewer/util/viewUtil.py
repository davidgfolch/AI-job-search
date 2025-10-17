from pandas import DataFrame
from ai_job_search.viewer.util.stStateUtil import setState
from ai_job_search.viewer.util.stUtil import scapeLatex
from ai_job_search.viewer.viewAndEditConstants import F_KEY_CLIENT, F_KEY_COMMENTS, F_KEY_COMPANY, F_KEY_SALARY, FF_KEY_PRESELECTED_ROWS
from ai_job_search.viewer.viewConstants import PAGE_STATE_KEY

KEY_SELECTED_IDS = 'selectedIds'


def mapDetailForm(jobData, fieldsBool):
    boolFieldsValues = []
    comments, salary, company, client = (None, None, None, None)
    if jobData:
        comments, salary, company, client = (jobData['comments'],
                                             jobData['salary'],
                                             jobData['company'],
                                             jobData['client'])
        setState(F_KEY_COMMENTS, comments)
        setState(F_KEY_SALARY, salary)
        setState(F_KEY_COMPANY, company)
        setState(F_KEY_CLIENT, client)
        boolMapper = map(lambda f: f if
                         jobData.get(f, False) else None,
                         fieldsBool)
        boolFieldsValues = list(filter(lambda x: x, boolMapper))
    comments = comments if comments else ''
    return boolFieldsValues, comments, salary, company, client


def getValuesAsDict(series: DataFrame, fields):
    res = {}
    for idx, f in enumerate(fields):
        value = series.iloc[idx]
        res[f] = getValueAsDict(f, value)
    return res


def getValueAsDict(f, value):
    if f == 'markdown' or f == 'comments':
        return value.decode('utf-8') if value else value
    return value.strip() if isinstance(value, str) else value


def formatDateTime(data: dict):
    data['dates'] = '\n  '.join(
        ['- <span style="font-size: small">' +
         f':green[{data[f].strftime("%d-%m-%y %H:%M")}] - {f}' +
         '</span>'
         for f in ['created', 'merged', 'modified'] if data[f] is not None])


def fmtDetailOpField(data: dict, key: str, label: str = None, level=0) -> str:
    value = data.get(key)
    if value is None:
        return ''
    label = key.capitalize() if label is None else label
    if isinstance(value,str):
        value = scapeLatex({key: value}, key).get(key)
    return f'{" "* level}- {label}: :green[{value}]\n'


def gotoPage(page, ids):
    setState(KEY_SELECTED_IDS, ids)
    setState(PAGE_STATE_KEY, page)


def gotoPageByUrl(page: int, linkText: str, ids: str, autoSelectFirst=True):
    if isinstance(ids, list):
        ids = ','.join([str(id) for id in ids])
    markdownUrl = f'[{linkText}](/?' + \
        '&'.join([f'{KEY_SELECTED_IDS}={ids}',
                  f'{PAGE_STATE_KEY}={page}'])
    if autoSelectFirst:
        markdownUrl += f'&{FF_KEY_PRESELECTED_ROWS}=0'
    return markdownUrl + ')'
