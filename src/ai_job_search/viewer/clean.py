import re
import streamlit as st
import pandas as pd
from ai_job_search.viewer.viewAndEdit import DB_FIELDS_BOOL, DB_FIELDS_MERGE
from ai_job_search.viewer.util.viewUtil import formatSql
from ai_job_search.viewer.util.stUtil import (
    KEY_SELECTED_IDS, PAGE_STATE_KEY, PAGE_VIEW_IDX,
    getState, setState, stripFields)
from tools.mysqlUtil import (MysqlUtil, deleteJobsQuery, updateFieldsQuery)

QUERY_DESCRIPTION = """Show all repeated job offers by `title,company`
 (excluding Joppy "company")"""
COLUMNS = stripFields('Counter,Ids,Title,Company')
IDS_IDX = 1
# TODO: HARCODED != Joppy because it could be many companies
# TODO: Make it configurable? in .venv file for ex. partial where filter
SELECT_DUPLICATED = """
select r.counter, r.ids, r.title, r.company
from (select count(*) as counter,
            GROUP_CONCAT(CAST(id as CHAR(50)) SEPARATOR ',') as ids,
            max(created) as max_created,  -- to delete all, but last
            title, company
        from jobs
        where company != 'Joppy'
        group by title, company
    ) as r
where r.counter>1
order by r.counter desc, r.title, r.company, r.max_created desc"""
DELETE_BY_IDS = 'delete from jobs where id in ({ids})'


def gotoPage(page, selectedRows):
    setState(KEY_SELECTED_IDS, getAllIds(selectedRows))
    setState(PAGE_STATE_KEY, page)


def getAllIds(selectedRows, dropFirstByGroup=False, plainIdsStr=True):
    rows = list(selectedRows.iloc[row].iloc[IDS_IDX]
                for row in range(len(selectedRows)))
    if len(rows) == 0:
        return None
    if dropFirstByGroup:
        rows = list({re.sub(r'^[0-9]+,', '', row) for row in rows})
    if plainIdsStr:
        ids = ','.join(rows)
        return ','.join(list(f"'{id}'" for id in ids.split(',')))
    return rows


def merge(selectedRows):
    rows = getAllIds(selectedRows, plainIdsStr=False)
    SELECT_FOR_MERGE = """select {cols}
        from jobs where id in ({ids})
        order by created asc"""
    cols = f'id, title, company,{DB_FIELDS_MERGE},{DB_FIELDS_BOOL}'
    colsArr = stripFields(cols)
    mysql = MysqlUtil()
    try:
        with st.container(height=400):
            for ids in rows:
                query = SELECT_FOR_MERGE.format(
                    **{'ids': ids,
                       'cols': cols})
                st.code(formatSql(query), 'sql')
                merged = {}
                for row in mysql.fetchAll(query):
                    for idx, f in enumerate(colsArr):
                        if idx >= 3 and row[idx]:
                            merged.setdefault(f, row[idx])
                    id = getFieldValue(row, colsArr, 'id')
                st.write(f'`{getFieldValue(row, colsArr, "title")}`',
                         '-',
                         f'`{getFieldValue(row, colsArr, "company")}`',
                         merged)
                query, params = updateFieldsQuery([id], merged)
                st.code(query, 'sql')
                queries = [{'query': query, 'params': params}]
                idsArr = removeNewestId(ids)
                query = deleteJobsQuery(idsArr)
                st.code(query, 'sql')
                queries.append({'query': query})
                affectedRows = mysql.executeAllAndCommit(queries)
                st.write(f'Affected rows (update & delete): {affectedRows}')
    finally:
        mysql.close()


def getFieldValue(row, colsArr, colName):
    return row[colsArr.index(colName)]


def removeNewestId(ids):
    idsArr = ids.split(',')
    idsArr.sort()
    idsArr.pop()
    return idsArr


def clean():
    mysql = MysqlUtil()
    try:
        query = SELECT_DUPLICATED.strip()
        with st.expander(QUERY_DESCRIPTION):
            if st.toggle('Edit query'):
                query = st.text_area('Query', query, key='cleanSelectQuery',
                                     height=300)
            st.code(query if query else SELECT_DUPLICATED.strip(), 'sql')
        df = pd.DataFrame(mysql.fetchAll(query), columns=COLUMNS)
        if len(df) > 0:
            dfWithSelections = df.copy()
            dfWithSelections.insert(
                0, "Sel", getState('selectAll', False))
            rows = st.data_editor(dfWithSelections, use_container_width=True,
                                  hide_index=True,
                                  key='cleanJobsListTable',
                                  column_config={'Ids': None}, height=400)
            selectedRows = df[rows.Sel]
            totalSelectedRows = len(selectedRows)
            ids = getAllIds(selectedRows)
            totalSelectedIds = len(ids.split(',')) if ids else 0
            st.write(f'{totalSelectedIds} selected jobs ',
                     f'({totalSelectedRows} selected rows)')
            c1, c2 = st.columns([3, 20])
            disabled = totalSelectedIds < 1
            c1.button('Select all', key='selectAll', type='primary')
            c1.button('Merge & Delete old duplicated in selection',
                      on_click=merge,
                      kwargs={'selectedRows': selectedRows},
                      type='primary', disabled=disabled)
            c1.button('View', on_click=gotoPage,
                      kwargs={'page': PAGE_VIEW_IDX,
                              'selectedRows': selectedRows},
                      type='primary', disabled=disabled)
            if not disabled:
                c2.dataframe(selectedRows, hide_index=True,
                             use_container_width=True)
        else:
            st.warning('No results found for query.')
    finally:
        mysql.close()
