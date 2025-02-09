import traceback
import streamlit as st
from ai_job_search.tools.mysqlUtil import (
    MysqlUtil, deleteJobsQuery, updateFieldsQuery)
# from ai_job_search.viewer.util.cleanUtil import getFieldValue, removeNewestId
from ai_job_search.tools.terminalColor import blue, cyan, printHR, red
from ai_job_search.tools.util import (
    AUTOMATIC_REPEATED_JOBS_MERGE, SHOW_SQL, removeNewLines)
from ai_job_search.viewer.util.cleanUtil import (
    getAllIds, getFieldValue, removeNewestId)
from ai_job_search.viewer.util.stUtil import showCodeSql, stripFields
from ai_job_search.viewer.viewAndEditConstants import (
    DB_FIELDS_BOOL)

DB_FIELDS_MERGE = """salary,required_technologies,optional_technologies,
ai_enriched,ai_enrich_error, company,client,comments,created"""
FIELDS_MERGE = stripFields(DB_FIELDS_MERGE)

INFO = "Show all repeated job offers by `title,company`"
COLUMNS = stripFields('Counter,Ids,Title,Company,Web Page')
IDS_IDX = 1
SELECT = """
select r.counter, r.ids, r.title, r.company, r.web_page
from (select count(*) as counter,
            GROUP_CONCAT(CAST(id as CHAR(50)) SEPARATOR ',') as ids,
            max(created) as max_created,  -- to delete all, but last
            title, company, web_page
        from jobs
        -- where company != 'Joppy'
        group by title, company, web_page
    ) as r
where r.counter>1
order by r.title, r.company, r.web_page, r.max_created desc"""
SELECT_FOR_MERGE = """select {cols}
    from jobs where id in ({ids})
    order by created asc"""
COLS = f'id, title,{DB_FIELDS_MERGE},{DB_FIELDS_BOOL}'
COLS_ARR = stripFields(COLS)
COLS_ARR.remove('closed')
COL_COMPANY_IDX = COLS_ARR.index('title')


def actionButton(stContainer, selectedRows, disabled):
    stContainer.button('Merge & Delete old duplicated in selection',
                       on_click=mergeStreamlitWrapper,
                       kwargs={'selectedRows': selectedRows},
                       type='primary', disabled=disabled)


def mergeStreamlitWrapper(selectedRows):
    rows = getAllIds(selectedRows, IDS_IDX, plainIdsStr=False)
    with st.container(height=400):
        for generatorResult in merge(rows):
            for line in generatorResult:
                if arr := line.get('arr', None):
                    [st.write(a) for a in arr]
                if txt := line.get('query', None):
                    showCodeSql(txt, True)
                if txt := line.get('text', None):
                    st.write(txt)


def merge(rows):
    mysql = MysqlUtil()
    try:
        for ids in rows:
            query = SELECT_FOR_MERGE.format(
                **{'ids': ids,
                    'cols': COLS})
            id, merged, out = mergeJobDuplicates(mysql.fetchAll(query), ids)
            updateQry, params = updateFieldsQuery([id], merged)
            queries = [{'query': updateQry, 'params': params}]
            idsArr = removeNewestId(ids)
            deleteQry = deleteJobsQuery(idsArr)
            queries.append({'query': deleteQry})
            affectedRows = mysql.executeAllAndCommit(queries)
            yield [{'arr': out, 'query': query}] + queries + [{
                'text': f'Affected rows (update & delete): {affectedRows}'}]

    finally:
        mysql.close()


def mergeJobDuplicates(rows, ids):
    merged: dict = {}
    for row in rows:
        for colIdx, f in enumerate(COLS_ARR):
            if colIdx > COL_COMPANY_IDX and row[colIdx]:
                if f != 'created' or \
                        f == 'created' and merged.get(f, None) is None:
                    merged.setdefault(f, row[colIdx])
        id = getFieldValue(row, COLS_ARR, 'id')
        out = [' '.join([f'`{getFieldValue(row, COLS_ARR, "title")}`',
                        '-',
                         f'`{getFieldValue(row, COLS_ARR, "company")}`',
                         f' (ids={ids})']),
               merged]
    return id, merged, out


def mergeDuplicatedJobs(rows):
    if not AUTOMATIC_REPEATED_JOBS_MERGE:
        return
    try:
        if len(rows) == 0:
            return
        rows = [row[IDS_IDX] for row in rows]
        printHR(cyan)
        print(cyan('Merging duplicated jobs (into the last created one) ',
                   'and deleting older ones...'))
        printHR(cyan)
        for generatorResult in merge(rows):
            for line in generatorResult:
                if arr := line.get('arr', None):
                    print(cyan(*[removeNewLines(f'{a}') for a in arr]))
                if txt := line.get('query', None) and SHOW_SQL:
                    print(blue(removeNewLines(txt)))
                if txt := line.get('text', None):
                    print(blue(removeNewLines(txt)))
    except Exception:
        print(red(traceback.format_exc()))
