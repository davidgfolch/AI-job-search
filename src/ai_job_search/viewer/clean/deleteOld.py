from pandas import DataFrame
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from ai_job_search.tools.mysqlUtil import MysqlUtil, deleteJobsQuery
from ai_job_search.viewer.clean.cleanUtil import getIdsIndex
from ai_job_search.viewer.util.stComponents import showCodeSql
from ai_job_search.viewer.util.stUtil import stripFields

DAYS = 10
DAYS2 = 20
INFO = f'Delete jobs (older than {DAYS} days and not applied)'
COLUMNS = stripFields('Id,Title,Company,Created')
SELECT = f"""
select id,title,company,created
from jobs
where (DATE(created) < DATE_SUB(CURDATE(), INTERVAL {DAYS} DAY) and
            not applied and not flagged and not seen) or
      (DATE(created) < DATE_SUB(CURDATE(), INTERVAL {DAYS2} DAY) and
            not applied and not flagged)
order by created desc
"""


def actionButton(container: DeltaGenerator, selectedRows, disabled):
    container.button('Delete old in selection',
                     on_click=delete,
                     kwargs={'selectedRows': selectedRows},
                     type='primary', disabled=disabled)


def delete(selectedRows: DataFrame):
    with MysqlUtil() as mysql:
        idsIdx = getIdsIndex(selectedRows)
        ids = list(selectedRows.iloc[row].iloc[idsIdx]
                   for row in range(len(selectedRows)))
        query = deleteJobsQuery(ids)
        showCodeSql(query, 'sql')
        count = mysql.executeAndCommit(query, {})
        st.info(f'Affected rows: {count}')
