from pandas import DataFrame
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from ai_job_search.tools.mysqlUtil import MysqlUtil, updateFieldsQuery
from ai_job_search.tools.util import getEnvMultiline
from ai_job_search.viewer.clean.cleanUtil import getIdsIndex
from ai_job_search.viewer.streamlitConn import mysqlCachedConnection
from ai_job_search.viewer.util.stComponents import showCodeSql
from ai_job_search.viewer.util.stUtil import stripFields


COLUMNS = stripFields('Id,Title,Company,Created')


def getTitleRegex():
    return getEnvMultiline('CLEAN_IGNORE_BY_TITLE_REGEX')


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


def actionButton(stContainer: DeltaGenerator, selectedRows, disabled):
    stContainer.button('Mark all ignored',
                       on_click=markIgnored,
                       kwargs={'selectedRows': selectedRows},
                       type='primary', disabled=disabled)


def markIgnored(selectedRows: DataFrame):
    idsIdx = getIdsIndex(selectedRows)
    ids = list(selectedRows.iloc[row].iloc[idsIdx]
               for row in range(len(selectedRows)))
    query, params = updateFieldsQuery(ids, {"ignored": True})
    showCodeSql(query, params)
    count = MysqlUtil(mysqlCachedConnection()).executeAndCommit(query, params)
    st.write(f'Affected rows: {count}')
