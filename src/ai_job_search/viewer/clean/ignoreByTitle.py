from pandas import DataFrame
import streamlit as st
from ai_job_search.tools.mysqlUtil import MysqlUtil, updateFieldsQuery
from ai_job_search.tools.util import getEnv
from ai_job_search.viewer.clean.cleanUtil import getIdsIndex
from ai_job_search.viewer.util.stComponents import showCodeSql
from ai_job_search.viewer.util.stUtil import stripFields


COLUMNS = stripFields('Id,Title,Company,Created')


def getTitleRegex():
    return getEnv('CLEAN_IGNORE_BY_TITLE_LOWER_REGEX')


def getInfo():
    return f'Ignore jobs (by title regex {getTitleRegex()})'


def getSelect():
    return f"""
        select id,title,company,created
        from jobs
        where LOWER(title) rlike '{getTitleRegex()}' and
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
