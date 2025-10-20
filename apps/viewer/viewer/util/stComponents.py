import streamlit as st
from collections import deque
from streamlit.delta_generator import DeltaGenerator

from commonlib.mysqlUtil import getColumnTranslated
from commonlib.sqlUtil import formatSql
from .historyUtil import historyButton
from .stStateUtil import getBoolKeyName, getState, listSessionFiles, loadSession, saveSession
from ..viewAndEditConstants import FF_KEY_CONFIG_PILLS


# TODO: modal -> try from streamlit_modal import Modal ??

def checkboxFilter(label, key, container: DeltaGenerator = st):
    return container.checkbox(label, key=getBoolKeyName(key))


def checkAndInput(label: str, key: str, withColumns=None, withContainer=True,
                  withHistory=False):
    c = st.container(border=1) if withContainer else st
    if not withColumns:
        enabled = checkboxFilter(label, key, c)
        col = c.columns([90, 15], vertical_alignment="top")
        col[0].text_input(label, key=key, disabled=not enabled,
                          label_visibility='collapsed')
        historyButton(key, withHistory, col[1])
    else:
        c = c.columns(withColumns, vertical_alignment="top")
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


def showCodeSql(sql: str, params: dict = None, format=False, showSql=None):
    showSqlToggle = 'showSql' in getState(FF_KEY_CONFIG_PILLS, [])
    if (showSql is not None and showSql) or showSqlToggle:
        if params:
            sql = sql.format(**params)
        if format:
            st.code(formatSql(sql), 'sql')
        else:
            st.code(sql, 'sql')


def reloadButton():
    if st.button("Reload"):
        st.rerun()


def sessionLoadSaveForm():
    options: deque = deque(listSessionFiles())
    options.remove('Default')
    options.append('(None)')
    options.append('Default')
    options.append('(New)')
    options.rotate(3)
    with st.container(border=1):
        c1, c2, c3 = st.columns([50, 5, 5], vertical_alignment='bottom')
        selected = c1.selectbox("Filters configurations",
                                options=options,
                                #  format_func=lambda i: os.path.split(i)[1],
                                #  label_visibility='collapsed',
                                key='currentSessionSaved')
        new = selected == '(New)'
        if new:
            selected = c1.text_input(
                'stateFile', label_visibility='collapsed',
                placeholder='new file name')
        kwargs = {'name': selected}
        c2.button('Save', on_click=saveSession,
                  key='sessionSaveButton', kwargs=kwargs)
        c3.button('Load', on_click=loadSession, key='sessionLoadButton',
                  kwargs=kwargs, disabled=new)
