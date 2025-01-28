import streamlit as st
from ai_job_search.tools.mysqlUtil import MysqlUtil, updateFieldsQuery
from ai_job_search.viewer.util.stUtil import showCodeSql, stripFields


INFO = 'Ignore internship jobs'
COLUMNS = stripFields('Id,Title,Company,Created')
IDS_IDX = 0
SELECT = """
select id,title,company,created
from jobs
where LOWER(title) rlike 'junior|internship|prácticas|becario' and
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
        ids = list(selectedRows.iloc[row].iloc[IDS_IDX]
                   for row in range(len(selectedRows)))
        query, params = updateFieldsQuery(ids, {"ignored": True})
        showCodeSql(query)
        count = mysql.executeAndCommit(query, params)
        st.write(f'Affected rows: {count}')
    finally:
        mysql.close()
