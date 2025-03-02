import streamlit as st
from streamlit.delta_generator import DeltaGenerator
import pandas as pd
from ai_job_search.viewer.clean import (
    deleteOld, ignoreByTitle, mergeDuplicates)
from ai_job_search.viewer.clean.cleanUtil import getAllIds
from ai_job_search.viewer.streamlitConn import mysqlCachedConnection
from ai_job_search.viewer.util.stComponents import showCodeSql
from ai_job_search.viewer.util.stUtil import (getState)
from ai_job_search.viewer.util.viewUtil import gotoPage
from ai_job_search.viewer.viewConstants import PAGE_VIEW_IDX
from tools.mysqlUtil import MysqlUtil


PROCESS_CONFIG = [
    {'info': mergeDuplicates.getInfo,
     'dfCols': mergeDuplicates.COLUMNS,
     'sql': mergeDuplicates.getSelect,
     'actionButtonFnc': mergeDuplicates.actionButton},
    {'info': ignoreByTitle.getInfo,
     'dfCols': ignoreByTitle.COLUMNS,
     'sql': ignoreByTitle.getSelect,
     'actionButtonFnc': ignoreByTitle.actionButton},
    {'info': deleteOld.getInfo,
     'dfCols': deleteOld.COLUMNS,
     'sql': deleteOld.getSelect,
     'actionButtonFnc': deleteOld.actionButton}
]


def clean():
    c1, c2 = st.columns([5, 5])
    idx = c1.selectbox("Select what to clean",
                       range(0, len(PROCESS_CONFIG)),
                       format_func=lambda i: PROCESS_CONFIG[i]['info'](),
                       label_visibility='collapsed',
                       key='selectedCleanProcess')
    cnf = PROCESS_CONFIG[idx]
    query = showQuery(c2, cnf['sql']())
    mysql = MysqlUtil(mysqlCachedConnection())
    rows = mysql.fetchAll(query)
    if len(rows) > 0:
        columns = mysql.getTableDdlColumnNames('jobs')
        rows, selectedRows = table(columns, cnf, rows)
        totalSelectedIds = tableSummary(rows, selectedRows)
        actionButtons(cnf, selectedRows, totalSelectedIds)
    else:
        st.warning('No results found for query.')


def table(columns, cnf, res):
    queryCols = cnf['dfCols']
    columns = queryCols if len(res[0]) == len(queryCols) \
        else columns
    df = pd.DataFrame(res, columns=columns)
    dfWithSelections = df.copy()
    defaultValue = getState('selectAll', False)
    dfWithSelections.insert(0, "Sel", defaultValue)
    rows = st.data_editor(dfWithSelections, use_container_width=True,
                          hide_index=True, key='cleanJobsListTable',
                          column_config={'Ids': None}, height=600)
    selectedRows = df[rows.Sel]
    return rows, selectedRows


def actionButtons(cnf, selectedRows, totalSelectedIds):
    c1, c2 = st.columns([3, 20])
    disabled = totalSelectedIds < 1
    c1.button('Select all', key='selectAll', type='primary')
    cnf['actionButtonFnc'](c1, selectedRows, disabled)
    c1.button('View', on_click=gotoPage,
              kwargs={'page': PAGE_VIEW_IDX,
                      'ids': getAllIds(selectedRows)},
              type='primary', disabled=disabled)
    if not disabled:
        c2.dataframe(selectedRows, hide_index=True,
                     use_container_width=True)


def tableSummary(rows, selectedRows):
    totalSelectedIds = countIds(selectedRows, True)
    totalSelectedRows = len(selectedRows)
    totalRows = len(rows)
    total = countIds(rows)
    txt = [f':green[{totalSelectedIds}/{total} JOBS selected/total]']
    if totalRows != total:
        txt.append(
            f' :blue[({totalSelectedRows}/{totalRows} ROWS selected/total)]')
    st.write(*txt)
    return totalSelectedIds


def countIds(rows: pd.DataFrame, selection=False):
    ids = getAllIds(rows)
    return len(ids.split(',')) if ids else 0


def showQuery(container: DeltaGenerator, q: str):
    with container.expander('Sql query details'):
        if st.toggle('Edit query'):
            q = st.text_area('Query', q, key='cleanSelectQuery', height=300)
        showCodeSql(q, True, True)
    return q
