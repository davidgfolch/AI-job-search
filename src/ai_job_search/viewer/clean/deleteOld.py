import streamlit as st
from ai_job_search.tools.mysqlUtil import MysqlUtil, deleteJobsQuery
from ai_job_search.viewer.util.stUtil import showCodeSql, stripFields

DAYS = 40
INFO = f'Delete jobs (older than {DAYS} days and not applied)'
COLUMNS = stripFields('Id,Title,Company,Created')
IDS_IDX = 0
SELECT = f"""

select id,title,company,created
from jobs
where DATE(created) < DATE_SUB(CURDATE(), INTERVAL {DAYS} DAY) and
(applied is null or applied=0) and
(ignored is null or ignored=0) and
(seen is null or seen=0)
order by created desc
"""


def actionButton(stContainer, selectedRows, disabled):
    stContainer.button('Delete old in selection',
                       on_click=delete,
                       kwargs={'selectedRows': selectedRows},
                       type='primary', disabled=disabled)


def delete(selectedRows):
    mysql = MysqlUtil()
    try:
        ids = list(selectedRows.iloc[row].iloc[IDS_IDX]
                   for row in range(len(selectedRows)))
        query = deleteJobsQuery(ids)
        showCodeSql(query, 'sql')
        count = mysql.executeAndCommit(query, {})
        st.info(f'Affected rows: {count}')
    finally:
        mysql.close()
