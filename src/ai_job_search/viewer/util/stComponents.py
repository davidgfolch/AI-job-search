import os
from pathlib import Path
import shlex
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
# TODO: modal -> try from streamlit_modal import Modal ??
from ai_job_search.tools.mysqlUtil import getColumnTranslated
from ai_job_search.tools.sqlUtil import formatSql
from ai_job_search.tools.util import SHOW_SQL, getEnvBool, listFiles
from ai_job_search.viewer.util.historyUtil import historyButton
from ai_job_search.viewer.util.stStateUtil import (
    getBoolKeyName,
    listSessionFiles,
    loadSession,
    saveSession)


def checkboxFilter(label, key, container: DeltaGenerator = st):
    return container.checkbox(label, key=getBoolKeyName(key))


def checkAndInput(label: str, key: str, withColumns=None, withContainer=True,
                  withHistory=False):
    c = st.container(border=1) if withContainer else st
    if not withColumns:
        enabled = checkboxFilter(label, key, c)
        col = c.columns([90, 10], vertical_alignment="top")
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


def showCodeSql(sql, format=False, showSql=False):
    if showSql or getEnvBool(SHOW_SQL):
        if format:
            st.code(formatSql(sql), 'sql')
        else:
            st.code(sql, 'sql')


def reloadButton():
    if st.button("Reload"):
        st.rerun()


def sessionStateButtons():
    options: list = listSessionFiles()
    options.append('(New)')
    with st.container(border=1):
        c = st.columns([50, 5, 5, 40], vertical_alignment='bottom')
        selected = c[0].selectbox("Filters configurations",
                                  options,
                                  format_func=lambda i: os.path.split(i)[1],
                                  #   label_visibility='collapsed',
                                  key='currentStateSaved')
        new = selected == '(New)'
        if new:
            selected = c[0].text_input(
                'stateFile', label_visibility='collapsed',
                placeholder='new file name')
        kwargs = {'name': selected}
        c[1].button('Save', on_click=saveSession, kwargs=kwargs)
        c[2].button('Load', on_click=loadSession, kwargs=kwargs,
                    disabled=new)
