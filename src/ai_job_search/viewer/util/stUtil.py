import re
from pandas import DataFrame
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
# TODO: modal -> try from streamlit_modal import Modal ??
from ai_job_search.tools.mysqlUtil import getColumnTranslated
from ai_job_search.tools.sqlUtil import formatSql
from ai_job_search.tools.util import SHOW_SQL
from ai_job_search.viewer.util.historyUtil import historyButton
from ai_job_search.viewer.util.stStateUtil import (
    getBoolKeyName, getState, setState)


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


def setMessageInfo(msg: str):
    setState('messageInfo', msg)


def getMessageInfo():
    msg = getState('messageInfo')
    if msg:
        st.session_state.pop('messageInfo')
    return msg


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


def scapeLatex(dictionary: dict, keys: list[str]):
    """Scape Latex symbols for Streamlit markdown"""
    for key in dictionary.keys():
        if key in keys:
            dictionary[key] = re.sub('\$', '\$', dictionary[key])
    return dictionary


# Components
def checkboxFilter(label, filterKey, container: DeltaGenerator = st):
    return container.checkbox(label, key=getBoolKeyName(filterKey))


def checkAndInput(label: str, key: str, inColumns=None, withContainer=True,
                  withHistory=False):
    c = st.container(border=1) if withContainer else st
    if not inColumns:
        enabled = checkboxFilter(label, key, c)
        col = c.columns([90, 10], vertical_alignment="top")
        col[0].text_input(label, key=key, disabled=not enabled,
                          label_visibility='collapsed')
        historyButton(key, withHistory, col[1])
    else:
        c = c.columns(inColumns, vertical_alignment="top")
        enabled = checkboxFilter(label, key, c[0])
        c[1].text_input(label, key=key, disabled=not enabled,
                        label_visibility='collapsed')
        historyButton(key, withHistory, c[2])


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


def showCodeSql(sql, format=False):
    if SHOW_SQL:
        if format:
            st.code(formatSql(sql), 'sql')
        else:
            st.code(sql, 'sql')
