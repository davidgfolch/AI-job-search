import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from pandas import DataFrame

from commonlib.mysqlUtil import MysqlUtil
from viewer.clean import deleteOld, ignoreByTitle
from viewer.clean.cleanUtil import getAllIds
from viewer.streamlitConn import mysqlCachedConnection
from viewer.util.stComponents import showCodeSql
from viewer.util.stStateUtil import getState, setState
from viewer.util.viewUtil import gotoPage
from viewer.viewConstants import PAGE_VIEW_IDX


PROCESS_CONFIG = [
    # {'info': mergeDuplicates.getInfo,
    #  'dfCols': mergeDuplicates.COLUMNS,
    #  'sql': mergeDuplicates.getSelect,
    #  'actionButtonFnc': mergeDuplicates.actionButton},
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
                       key='selectedCleanProcess',
                       on_change=resetState)
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


def resetState():
    setState('lastSelected', None)


def table(columns, cnf, res):
    queryCols = cnf['dfCols']
    columns = queryCols if len(res[0]) == len(queryCols) else columns
    df = DataFrame(res, columns=columns)
    df.insert(0, "Sel", False)
    lastSelected = getState('lastSelected')
    if getState('selectAll'):
        df['Sel'] = True
        setState('lastSelected', {'Sel': df['Sel']})
    elif lastSelected and 'Sel' in lastSelected:
        df['Sel'] = lastSelected['Sel']
        
    #st.write(f'df: {df["Sel"]}')
    colsConfig = {'Ids': None,
                  'Sel': st.column_config.Column(width='small'),
                  'Id': st.column_config.Column(width='small'),
                  'Title': st.column_config.Column(width='large'),
                  'Company': st.column_config.Column(width='large'),
                  'Created': st.column_config.Column(width='large'),
                  }
    #TODO: use st-aggrid instead of data_editor?
    editedDf = st.data_editor(df, width='stretch',
                          hide_index=True, key='cleanJobsListTable',
                          on_change=onTableChange,
                          column_config=colsConfig, height=600)
    #FIXME: when doing ignore rows first -> select all,
    selectedRows = df[editedDf['Sel']]
    return editedDf, selectedRows


def onTableChange():
    selected = getState('cleanJobsListTable')['edited_rows']
    lastSelected = getState('lastSelected')
    if lastSelected and selected and selected != lastSelected:
        lastSelected.update(selected)
        setState('lastSelected', lastSelected)
    else:
        setState('lastSelected', selected)


def actionButtons(cnf, selectedRows, totalSelectedIds):
    c1, c2 = st.columns([3, 20])
    disabled = totalSelectedIds < 1
    c1.button('Select all', key='selectAll', type='primary')
    cnf['actionButtonFnc'](c1, selectedRows, disabled)
    c1.button('View', on_click=gotoPage, type='primary', disabled=disabled,
              kwargs={'page': PAGE_VIEW_IDX,
                      'ids': getAllIds(selectedRows)})
    if not disabled:
        c2.dataframe(selectedRows, hide_index=True, width='stretch')


def tableSummary(rows, selectedRows):
    totalSelectedIds = countIds(selectedRows, True)
    totalSelectedRows = len(selectedRows)
    totalRows = len(rows)
    total = countIds(rows)
    txt = [f':green[{totalSelectedIds}/{total} JOBS selected/total]']
    if totalRows != total:
        txt.append(f' :blue[({totalSelectedRows}/{totalRows} ROWS selected/total)]')
    st.write(*txt)
    return totalSelectedIds


def countIds(rows: DataFrame, selection=False):
    ids = getAllIds(rows)
    return len(ids.split(',')) if ids else 0


def showQuery(container: DeltaGenerator, q: str):
    with container.expander('Sql query details'):
        if st.toggle('Edit query'):
            q = st.text_area('Query', q, key='cleanSelectQuery', height=300)
        showCodeSql(q, True, True)
    return q
