import streamlit as st
from ai_job_search.tools.mysqlUtil import (
    MysqlUtil, deleteJobsQuery, updateFieldsQuery)
# from ai_job_search.viewer.util.cleanUtil import getFieldValue, removeNewestId
from ai_job_search.viewer.util.cleanUtil import (
    getAllIds, getFieldValue, removeNewestId)
from ai_job_search.viewer.util.stUtil import formatSql, showCodeSql, stripFields
from ai_job_search.viewer.viewAndEditConstants import (
    DB_FIELDS_BOOL, DB_FIELDS_MERGE)


INFO = "Show all repeated job offers by `title,company`"
COLUMNS = stripFields('Counter,Ids,Title,Company')
IDS_IDX = 1
SELECT = """
select r.counter, r.ids, r.title, r.company
from (select count(*) as counter,
            GROUP_CONCAT(CAST(id as CHAR(50)) SEPARATOR ',') as ids,
            max(created) as max_created,  -- to delete all, but last
            title, company
        from jobs
        -- where company != 'Joppy'
        group by title, company
    ) as r
where r.counter>1
order by r.counter desc, r.title, r.company, r.max_created desc"""
SELECT_FOR_MERGE = """select {cols}
    from jobs where id in ({ids})
    order by created asc"""


def actionButton(stContainer, selectedRows, disabled):
    stContainer.button('Merge & Delete old duplicated in selection',
                       on_click=merge,
                       kwargs={'selectedRows': selectedRows},
                       type='primary', disabled=disabled)


def merge(selectedRows):
    rows = getAllIds(selectedRows, IDS_IDX, plainIdsStr=False)
    cols = f'id, title,{DB_FIELDS_MERGE},{DB_FIELDS_BOOL}'
    colsArr = stripFields(cols)
    colsArr.remove('closed')
    colCompanyIdx = colsArr.index('title')
    mysql = MysqlUtil()
    try:
        with st.container(height=400):
            for ids in rows:
                query = SELECT_FOR_MERGE.format(
                    **{'ids': ids,
                       'cols': cols})
                showCodeSql(query, True)
                merged = {}
                for row in mysql.fetchAll(query):
                    for idx, f in enumerate(colsArr):
                        if idx > colCompanyIdx and row[idx]:
                            merged.setdefault(f, row[idx])
                    id = getFieldValue(row, colsArr, 'id')
                st.write(f'`{getFieldValue(row, colsArr, "title")}`',
                         '-',
                         f'`{getFieldValue(row, colsArr, "company")}`',
                         merged)
                updateQry, params = updateFieldsQuery([id], merged)
                showCodeSql(updateQry)
                queries = [{'query': updateQry, 'params': params}]
                idsArr = removeNewestId(ids)
                deleteQry = deleteJobsQuery(idsArr)
                showCodeSql(deleteQry)
                queries.append({'query': deleteQry})
                affectedRows = mysql.executeAllAndCommit(queries)
                st.write(f'Affected rows (update & delete): {affectedRows}')
    finally:
        mysql.close()
