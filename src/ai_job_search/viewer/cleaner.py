import streamlit as st
import pandas as pd
from ai_job_search.viewer.clean import (
    deleteOld, ignoreInternships, mergeDuplicateds)
from ai_job_search.viewer.util.cleanUtil import (getAllIds, gotoPage)
from ai_job_search.viewer.util.stUtil import (PAGE_VIEW_IDX, getState)
from tools.mysqlUtil import (MysqlUtil)


QUERIES = [
    {'info': mergeDuplicateds.INFO,
     'dfCols': mergeDuplicateds.COLUMNS,
     'sql': mergeDuplicateds.SELECT,
     'idsIndex': mergeDuplicateds.IDS_IDX,
     'actionButtonFnc': mergeDuplicateds.actionButton},
    {'info': ignoreInternships.INFO,
     'dfCols': ignoreInternships.COLUMNS,
     'sql': ignoreInternships.SELECT,
     'idsIndex': ignoreInternships.IDS_IDX,
     'actionButtonFnc': ignoreInternships.actionButton},
    {'info': deleteOld.INFO,
     'dfCols': deleteOld.COLUMNS,
     'sql': deleteOld.SELECT,
     'idsIndex': deleteOld.IDS_IDX,
     'actionButtonFnc': deleteOld.actionButton}
]


def clean():
    mysql = MysqlUtil()
    try:
        c1, c2 = st.columns([5, 5])
        processIdx = c1.selectbox("Select what to clean",
                                  range(0, len(QUERIES)),
                                  format_func=lambda i: QUERIES[i]['info'],
                                  label_visibility='collapsed',
                                  key='selectedCleanProcess')
        query = QUERIES[processIdx]['sql']
        with c2.expander('Sql query details'):
            fmtQuery = QUERIES[processIdx]['sql'].strip()
            if st.toggle('Edit query'):
                query = st.text_area('Query', query, key='cleanSelectQuery',
                                     height=300)
            st.code(query if query else fmtQuery, 'sql')
        res = mysql.fetchAll(query)
        if len(res) > 0:
            if len(res[0]) == len(QUERIES[processIdx]['dfCols']):
                df = pd.DataFrame(mysql.fetchAll(query),
                                  columns=QUERIES[processIdx]['dfCols'])
            else:
                df = pd.DataFrame(mysql.fetchAll(query),
                                  columns=mysql.getTableDdlColumnNames('jobs'))
            dfWithSelections = df.copy()
            dfWithSelections.insert(
                0, "Sel", getState('selectAll', False))
            rows = st.data_editor(dfWithSelections, use_container_width=True,
                                  hide_index=True,
                                  key='cleanJobsListTable',
                                  column_config={'Ids': None}, height=400)
            selectedRows = df[rows.Sel]
            totalSelectedRows = len(selectedRows)
            idsIndex = QUERIES[processIdx]['idsIndex']
            ids = getAllIds(selectedRows, idsIndex)
            total = len(getAllIds(rows, idsIndex))
            totalSelectedIds = len(ids.split(',')) if ids else 0
            if totalSelectedRows == totalSelectedIds:
                st.write(f'{totalSelectedIds}/{total} selected/total jobs ')
            else:
                st.write(f'{totalSelectedIds}/{total} selected/total jobs ',
                         f'({totalSelectedRows} selected rows)')
            c1, c2 = st.columns([3, 20])
            disabled = totalSelectedIds < 1
            c1.button('Select all', key='selectAll', type='primary')
            QUERIES[processIdx]['actionButtonFnc'](c1, selectedRows, disabled)
            c1.button('View', on_click=gotoPage,
                      kwargs={'page': PAGE_VIEW_IDX,
                              'selectedRows': selectedRows,
                              'idsIndex': idsIndex},
                      type='primary', disabled=disabled)
            if not disabled:
                c2.dataframe(selectedRows, hide_index=True,
                             use_container_width=True)
        else:
            st.warning('No results found for query.')
    finally:
        mysql.close()
