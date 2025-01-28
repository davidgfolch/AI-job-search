import re
import streamlit as st
from pandas import DataFrame

from ai_job_search.viewer.util.stUtil import scapeLatex, setState
from ai_job_search.viewer.viewAndEditConstants import DETAIL_FORMAT


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
        data[f'{f}Time'] = data[f].time()
        data[f] = data[f].date()
    if data['created'] == data['modified']:
        data['modified'] = None
        if data['createdTime'] == data['modifiedTime']:
            data['modifiedTime'] = None
    data['modified'] = ' - '.join([str(x) for x in [data['modified'], data['modifiedTime']] if x is not None])


def formatDetail(jobData: dict):
    data = scapeLatex(jobData)
    formatDateTime(jobData)
    data = {k: (data[k] if data[k] else None)
            for k in data.keys()}
    data = scapeTilde(data)
    str = DETAIL_FORMAT.format(**data)
    str += fmtDetailOpField(data, 'client')
    str += fmtDetailOpField(data, 'salary')
    reqSkills = fmtDetailOpField(data, 'required_technologies', 'Required', 2)
    opSkills = fmtDetailOpField(data, 'optional_technologies', 'Optional', 2)
    if reqSkills + opSkills != '':
        str += ''.join(["- Skills\n", reqSkills, opSkills])
    st.markdown(str)
    if val := data.get('comments'):
        with st.expander('Comments', expanded=True):
            st.markdown(val)
    st.markdown(data['markdown'])


def fmtDetailOpField(data: dict, key: str, label: str = None, level=0) -> str:
    value = data.get(key)
    if value is None:
        return ''
    label = key.capitalize() if label is None else label
    return f'{" "* level}- {label}: `{data.get(key)}`\n'


def scapeTilde(data):
    # - Source: `{web_page}`
    # - Company: `{company}`
    # - Client: `{client}`
    # - Salary: `{salary}`
    # - Skills
    #   - Required: `{required_technologies}`
    #   - Optional: `{optional_technologies}`
    DETAIL_SCAPED_FIELDS = ['company', 'client', 'salary',
                            'required_technologies', 'optional_technologies']
    return {k: (re.sub('`', "'", data[k])
                if k in DETAIL_SCAPED_FIELDS and data.get(k) is not None
                else data[k])
            for k in data.keys()}
