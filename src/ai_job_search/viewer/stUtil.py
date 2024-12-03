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


def getState(key: str):
    return st.session_state[key]


def getStateOrDefault(key: str, default=None):
    return st.session_state.get(key, default)


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
    value = getStateOrDefault(key, default)
    isStr = isinstance(value, str)
    strHasLen = not isStr or (isStr and len(value.strip()) > 0)
    if setEmpty or (value and strHasLen):
        fieldsValues[key] = value


def pillsValuesToDict(key, fields):
    value = getStateOrDefault(key, None)
    if value:
        return {fields[i]: fields[i] in value for i in range(len(fields))}
    return {}


def getSelectedRowsIds(key):
    selectedRows: DataFrame = getStateOrDefault(key, None)
    return list(selectedRows.iloc[idx]['id'] for idx in range(len(selectedRows)))


def scapeLatex(dictionary: dict):
    """Scape Latex symbols for Streamlit markdown"""
    for key in dictionary.keys():
        if (key == 'markdown'):
            dictionary[key] = re.sub(r'[$]', '\\$', dictionary[key])
    return dictionary


def getAndFilter(pills, value):
    filters = ' and '.join(list(map(lambda f: f'{f}={value}', pills)))
    return f' and ({filters})' if filters else ''


# Components
def checkboxNoLabel(label, key):
    return st.checkbox(label, key=key, label_visibility='collapsed')


def checkAndInput(label: str, checkKey: str, inputKey: str):
    c1, c2 = st.columns([1, 90], vertical_alignment="bottom")
    with c1:
        res1 = checkboxNoLabel(label, checkKey)
    with c2:
        res2 = st.text_input(label, key=inputKey, disabled=not res1)
    return res1, res2
