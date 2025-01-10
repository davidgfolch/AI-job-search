import streamlit as st
from ai_job_search.tools.mysqlUtil import MysqlUtil, updateFieldsQuery
from ai_job_search.viewer.util.stUtil import stripFields


INFO = 'Ignore internship jobs'
COLUMNS = stripFields('Id,Title,Company,Created')
IDS_IDX = 0
SELECT = """
select id,title,company,created
from jobs
where LOWER(title) rlike 'internship' and
        not (ignored or applied)
order by created desc
"""


def actionButton(stContainer, selectedRows, disabled):
    stContainer.button('Mark all ignored',
                       on_click=markIgnored,
                       kwargs={'selectedRows': selectedRows},
                       type='primary', disabled=disabled)


def markIgnored(selectedRows):
    mysql = MysqlUtil()
    try:
        with st.container(height=400):
            ids = list(selectedRows.iloc[row].iloc[IDS_IDX]
                       for row in range(len(selectedRows)))
            query, params = updateFieldsQuery(ids, {"ignored": True})
            st.code(query, 'sql')
            count = mysql.executeAndCommit(query, params)
            st.write(f'Affected rows: {count}')
    finally:
        mysql.close()
