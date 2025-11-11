import traceback

from ai_job_search.tools.mysqlUtil import MysqlUtil, deleteJobsQuery, updateFieldsQuery
from ai_job_search.tools.terminalColor import blue, cyan, red
from ai_job_search.tools.util import getEnvBool, removeNewLines
from ai_job_search.viewer.clean.cleanUtil import getFieldValue
from ai_job_search.viewer.util.stUtil import stripFields
from ai_job_search.viewer.viewAndEditConstants import DB_FIELDS_BOOL


DB_FIELDS_MERGE = """salary,required_technologies,optional_technologies,
ai_enriched,ai_enrich_error,company,client,comments, created"""
FIELDS_MERGE = stripFields(DB_FIELDS_MERGE)
COLUMNS = stripFields('Counter,Ids,Title,Company')
SELECT_FOR_MERGE = """select {cols}
    from jobs where id in ({ids})
    order by created asc"""
COLS = f'id, title,{DB_FIELDS_MERGE},{DB_FIELDS_BOOL}'
COLS_ARR = stripFields(COLS)
COLS_ARR.remove('closed')
COL_COMPANY_IDX = COLS_ARR.index('title')


def getInfo():
    return "Merge duplicated jobs by `title,company`"


def getSelect():
    return """
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
    order by r.title, r.company, r.max_created desc"""


def merge(mysql: MysqlUtil, rowsIds) -> list:
    results = []
    for ids in rowsIds:
        query = SELECT_FOR_MERGE.format(**{'ids': ids,'cols': COLS})
        id, merged, out = mergeJobDuplicates(mysql.fetchAll(query), ids)
        updateQry, params = updateFieldsQuery([id], merged, merged=True)
        queries = [{'query': updateQry, 'params': params}]
        idsArr = ids.split(',')
        idsArr.remove(str(id))
        deleteQry = deleteJobsQuery(idsArr)
        queries.append({'query': deleteQry})
        affectedRows = mysql.executeAllAndCommit(queries)
        results.append([{'arr': out, 'query': query}] + queries + [{
            'text': f'Merge duplicates: affected rows (updated {id} & deleted {idsArr}):' +
            f' {affectedRows}'}])
    return results


def mergeJobDuplicates(rows, ids):
    merged: dict = {}
    for row in rows:
        for colIdx, f in enumerate(COLS_ARR):
            if colIdx > COL_COMPANY_IDX and row[colIdx]:
                if f != 'created' or f == 'created' and merged.get(f, None) is None:
                    merged[f] = row[colIdx]
        id = getFieldValue(row, COLS_ARR, 'id')
        out = [' '.join([f'`{getFieldValue(row, COLS_ARR, "title")}`',
                        '-',
                         f'`{getFieldValue(row, COLS_ARR, "company")}`',
                         f' (ids={ids})']),
               merged]
    return id, merged, out

