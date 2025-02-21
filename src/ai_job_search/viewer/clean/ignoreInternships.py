from pandas import DataFrame
import streamlit as st
from ai_job_search.tools.mysqlUtil import MysqlUtil, updateFieldsQuery
from ai_job_search.tools.util import getEnv
from ai_job_search.viewer.clean.cleanUtil import getIdsIndex
from ai_job_search.viewer.util.stComponents import showCodeSql
from ai_job_search.viewer.util.stUtil import stripFields


TITLE_REGEX = getEnv('CLEAN_MARK_IGNORED_BY_TITLE_LOWER_REGEX')
INFO = f'Ignore jobs (by title regex {TITLE_REGEX})'
COLUMNS = stripFields('Id,Title,Company,Created')
SELECT = f"""
select id,title,company,created
from jobs
where LOWER(title) rlike '{TITLE_REGEX}' and
        not (ignored or applied)
order by created desc
"""


def actionButton(stContainer, selectedRows, disabled):
    stContainer.button('Mark all ignored',
                       on_click=markIgnored,
                       kwargs={'selectedRows': selectedRows},
                       type='primary', disabled=disabled)


def markIgnored(selectedRows: DataFrame):
    with MysqlUtil() as mysql:
        idsIdx = getIdsIndex(selectedRows)
        ids = list(selectedRows.iloc[row].iloc[idsIdx]
                   for row in range(len(selectedRows)))
        query, params = updateFieldsQuery(ids, {"ignored": True})
        showCodeSql(query)
        count = mysql.executeAndCommit(query, params)
        st.write(f'Affected rows: {count}')
