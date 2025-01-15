from functools import reduce
import re
from pandas import DataFrame
import streamlit as st

from ai_job_search.tools.mysqlUtil import getColumnTranslated


# Application pages & state keys
PAGE_STATE_KEY = 'selectedPage'
PAGE_VIEW = "View & manage"
PAGE_CLEAN = "Clean data"
PAGE_VIEW_IDX = 0
PAGE_CLEAN_IDX = 1
KEY_SELECTED_IDS = 'selectedIds'

PAGES = {
    PAGE_VIEW_IDX: PAGE_VIEW,
    PAGE_CLEAN_IDX: PAGE_CLEAN,
}


# States
def initStates(keyValue: dict):
    for k in keyValue.keys():
        if k not in st.session_state:
            st.session_state[k] = keyValue[k]


def getState(key: str, default=None):
    value = st.session_state.get(key, default)
    if (isinstance(value, DataFrame) and len(value)) or value:
        if isinstance(value, str):
            if len(value.strip()) > 0:
                return value
        else:
            return value
    return default


def getStateBool(*keys: str, default=False) -> bool:
    return reduce(
        lambda x, y: x and y,
        (st.session_state.get(getBoolKeyName(key), default) for key in keys))


def getStateBoolValue(*keys: str):
    return reduce(lambda x, y: x and y,
                  (getStateBool(key) and getState(key) for key in keys))


def setState(key: str, value):
    st.session_state[key] = value


def setMessageInfo(msg: str):
    setState('messageInfo', msg)


def getMessageInfo():
    return getState('messageInfo')


# Fields processing
def stripFields(fields: str) -> list[str]:
    return list(map(lambda c: re.sub('\n', '', c.strip()), fields.split(',')))


def sortFields(fields: str, sortFields: str):
    fArr = stripFields(fields)
    sArr = stripFields(sortFields)
    res = []
    for s in sArr:
        fArr.remove(s)
        res.append(s)
    for f in fArr:
        res.append(f)
    return ','.join(res)


def setFieldValue(fieldsValues, key, default=None, setEmpty: bool = False):
    value = getState(key, default)
    isStr = isinstance(value, str)
    strHasLen = not isStr or (isStr and len(value.strip()) > 0)
    if setEmpty or (value and strHasLen):
        fieldsValues[key] = value


def pillsValuesToDict(key, fields):
    value = getState(key, None)
    if value:
        return {fields[i]: fields[i] in value for i in range(len(fields))}
    return {}


def getSelectedRowsIds(key):
    selectedRows: DataFrame = getState(key, None)
    return list(
        selectedRows.iloc[idx]['id'] for idx in range(len(selectedRows)))


def scapeLatex(dictionary: dict):
    """Scape Latex symbols for Streamlit markdown"""
    for key in dictionary.keys():
        if (key == 'markdown'):
            dictionary[key] = re.sub(r'[$]', '\\$', dictionary[key])
    return dictionary


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


# Components
def checkboxFilter(label, filterKey, container=st):
    return container.checkbox(label, key=getBoolKeyName(filterKey))


def getBoolKeyName(key: str):
    return f'is{key.capitalize()}'


def checkAndInput(label: str, key: str, inColumns=None, withContainer=True):
    c = st
    if withContainer:
        c = st.container(border=1)
    if not inColumns:
        enabled = checkboxFilter(label, key, c)
        c.text_input(label, key=key, disabled=not enabled,
                     label_visibility='collapsed')
    else:
        c1, c2 = c.columns(inColumns, vertical_alignment="top")
        with c1:
            enabled = checkboxFilter(label, key, c)
        c2.text_input(label, key=key, disabled=not enabled,
                      label_visibility='collapsed')


def checkAndPills(label, fields: list[str], key: str):
    with st.container(border=1):
        c1, c2 = st.columns([4, 25], vertical_alignment="top")
        with c1:
            enabled = checkboxFilter(label, key)
        with c2:
            st.pills(label, fields, key=key,
                     format_func=lambda c: getColumnTranslated(c),
                     selection_mode='multi', disabled=not enabled,
                     label_visibility='collapsed')


# Sql format
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
