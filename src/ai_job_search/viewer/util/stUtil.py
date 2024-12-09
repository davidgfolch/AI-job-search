from functools import reduce
import re
from pandas import DataFrame
import streamlit as st


# Application pages & state keys
PAGE_STATE_KEY = 'selectedPage'
PAGE_VIEW = "View & manage"
PAGE_CLEAN = "Clean data"
KEY_SELECTED_IDS = 'selectedIds'


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


# Fields processings
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
    return list(selectedRows.iloc[idx]['id'] for idx in range(len(selectedRows)))


def scapeLatex(dictionary: dict):
    """Scape Latex symbols for Streamlit markdown"""
    for key in dictionary.keys():
        if (key == 'markdown'):
            dictionary[key] = re.sub(r'[$]', '\\$', dictionary[key])
    return dictionary


def getAndFilter(pills, value):
    if not pills:
        return ''
    filters = ' and '.join(list(map(lambda f: f'{f}', pills)))
    if filters:
        if not value:
            return f' and not ({filters})'
        else:
            return f' and ({filters})'
    return ''


# Components
def checkboxNoLabel(label, key):
    return st.checkbox(label, key=key, label_visibility='collapsed')


def getBoolKeyName(key: str):
    return f'is{key.capitalize()}'


def checkAndInput(label: str, key: str):
    c1, c2 = st.columns([1, 90], vertical_alignment="top")
    with c1:
        enabled = checkboxNoLabel(label, getBoolKeyName(key))
    with c2:
        st.text_input(label, key=key, disabled=not enabled)


def checkAndPills(label, fields: list[str], key: str):
    c1, c2 = st.columns([1, 90], vertical_alignment="top")
    with c1:
        enabled = checkboxNoLabel(label, getBoolKeyName(key))
    with c2:
        st.pills(label, fields, key=key,
                 selection_mode='multi', disabled=not enabled)
