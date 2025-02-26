import re
from pandas import DataFrame
import streamlit as st
# TODO: modal -> try from streamlit_modal import Modal ??
from ai_job_search.viewer.util.stStateUtil import (
    getState, setState)


def setMessageInfo(msg: str):
    setState('messageInfo', msg)


def getMessageInfo():
    msg = getState('messageInfo')
    if msg:
        st.session_state.pop('messageInfo')
    return msg


def getTextAreaHeightByText(comments, defaultRows=5, defaultHeight=600):
    rows = defaultRows if comments is None else len(comments.split('\n'))
    rows = rows if rows >= defaultRows else defaultRows
    return rows*28 if rows*28 < defaultHeight else defaultHeight


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


def inColumns(columns: list[tuple], kwargs={}):
    """ columns: [
      (size_int, lambda _: st.button(xxxx),
      (size_int, lambda _: fncUsingStreamlitCompoenents(xxxx), ...]"""
    c = st.columns([col[0] for col in columns], **kwargs)
    for idx, col in enumerate(columns):
        with c[idx]:
            col[1](c[idx])
