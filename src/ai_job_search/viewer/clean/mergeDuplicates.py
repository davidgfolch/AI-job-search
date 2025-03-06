import traceback
from ai_job_search.tools.mysqlUtil import (
    MysqlUtil, deleteJobsQuery, updateFieldsQuery)
from ai_job_search.tools.terminalColor import blue, cyan, red
from ai_job_search.tools.util import (
    SHOW_SQL_IN_AI_ENRICHMENT, getEnvBool,
    removeNewLines)
from ai_job_search.viewer.clean.cleanUtil import (
    getFieldValue, removeNewestId)
from ai_job_search.viewer.util.stUtil import stripFields
from ai_job_search.viewer.viewAndEditConstants import (
    DB_FIELDS_BOOL)


DB_FIELDS_MERGE = """salary,required_technologies,optional_technologies,
ai_enriched,ai_enrich_error,company,client,comments"""
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


def merge(rows):
    with MysqlUtil() as mysql:
        for ids in rows:
            query = SELECT_FOR_MERGE.format(
                **{'ids': ids,
                    'cols': COLS})
            id, merged, out = mergeJobDuplicates(mysql.fetchAll(query), ids)
            updateQry, params = updateFieldsQuery([id], merged, merged=True)
            queries = [{'query': updateQry, 'params': params}]
            idsArr = removeNewestId(ids)
            deleteQry = deleteJobsQuery(idsArr)
            queries.append({'query': deleteQry})
            affectedRows = mysql.executeAllAndCommit(queries)
            yield [{'arr': out, 'query': query}] + queries + [{
                'text': f'Affected rows (update & delete): {affectedRows}'}]


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
    """Scrapper ai enrichment entry"""
    try:
        if len(rows) == 0:
            return
        idsIdx = 1
        rows = [row[idsIdx] for row in rows]
        for generatorResult in merge(rows):
            for line in generatorResult:
                print(' ', end='')
                if arr := line.get('arr', None):
                    print(cyan(' '.join([removeNewLines(a) for a in arr])),
                          end=' ')
                query = line.get('query', None)
                if getEnvBool(SHOW_SQL_IN_AI_ENRICHMENT) and query:
                    print(blue(removeNewLines(query)), end=' ')
                if txt := line.get('text', None):
                    print(blue(removeNewLines(txt)), end=' ')
    except Exception:
        print(red(traceback.format_exc()))
