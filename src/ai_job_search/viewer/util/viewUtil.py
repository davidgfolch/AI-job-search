import streamlit as st
from pandas import DataFrame, Timestamp

from ai_job_search.viewer.util.stUtil import (
    KEY_SELECTED_IDS, PAGE_STATE_KEY, scapeLatex, setState)
from ai_job_search.viewer.viewAndEditConstants import (
    DETAIL_FORMAT, FF_KEY_PRESELECTED_ROWS)


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


def getValuesAsDict(series: DataFrame, fields):
    res = {}
    for idx, f in enumerate(fields):
        value = series.iloc[idx]
        if f == 'markdown' or f == 'comments':
            res[f] = value.decode('utf-8') if value else value
        else:
            res[f] = value.strip() if isinstance(value, str) else value
    return res


def formatDateTime(data: dict):
    for f in ['created', 'modified']:
        if isinstance(data[f], Timestamp):
            data[f'{f}Time'] = f'🕑 {data[f].time()}'
            data[f] = f'📅 {data[f].date()}'
        else:
            data[f] = None
            data[f'{f}Time'] = None
    if data['created'] == data['modified']:
        data['modified'] = None
        if data['createdTime'] == data['modifiedTime']:
            data['modifiedTime'] = None
    data['modified'] = ''.join(
        [str(x)
         for x in [data['modified'], data['modifiedTime']] if x is not None])


def formatDetail(jobData: dict):
    data = scapeLatex(jobData, 'markdown')
    formatDateTime(jobData)
    data = {k: (data[k] if data[k] else None)
            for k in data.keys()}
    str = DETAIL_FORMAT.format(**data)
    str += fmtDetailOpField(data, 'client')
    str += fmtDetailOpField(data, 'salary')
    reqSkills = fmtDetailOpField(data, 'required_technologies', 'Required', 2)
    opSkills = fmtDetailOpField(data, 'optional_technologies', 'Optional', 2)
    if reqSkills + opSkills != '':
        str += ''.join(["- Skills\n", reqSkills, opSkills])
    st.write(str)
    if val := data.get('comments'):
        with st.expander('Comments', expanded=True):
            st.markdown(val)
    st.markdown(data['markdown'])


def fmtDetailOpField(data: dict, key: str, label: str = None, level=0) -> str:
    value = data.get(key)
    if value is None:
        return ''
    label = key.capitalize() if label is None else label
    value = scapeLatex({key: data.get(key)}, key).get(key)
    return f'{" "* level}- {label}: :green[{value}]\n'


def gotoPage(page, ids):
    setState(KEY_SELECTED_IDS, ids)
    setState(PAGE_STATE_KEY, page)


def gotoPageByUrl(page: int, linkText: str, ids: str, autoSelectFirst=True):
    print(f'ids type = {type(ids)}')
    if isinstance(ids, list):
        ids = ','.join([str(id) for id in ids])
        print(f'ids type = {type(ids)}')
    markdownUrl = f'[{linkText}](/?{KEY_SELECTED_IDS}={ids}&{PAGE_STATE_KEY}={page}'
    markdownUrl += (f'&{FF_KEY_PRESELECTED_ROWS}=0' if autoSelectFirst else '') + ')'
    return markdownUrl
