import streamlit as st
from ai_job_search.tools.mysqlUtil import MysqlUtil, deleteJobsQuery
from ai_job_search.viewer.util.stUtil import showCodeSql, stripFields


INFO = 'Delete oldest ignored jobs'
COLUMNS = stripFields('Id,Title,Company,Applied,Created')
IDS_IDX = 0
SELECT = """
select id,title,company,comments,created
from jobs
where DATE(created) < DATE_SUB(CURDATE(), INTERVAL 60 DAY) and
    (not applied and ignored) and comments is null
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
