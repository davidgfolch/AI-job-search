from pandas import DataFrame
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from commonlib.mysqlUtil import MysqlUtil
from commonlib.sqlUtil import updateFieldsQuery
from commonlib.util import getEnvMultiline
from .cleanUtil import getIdsIndex
from ..mysqlConn import mysqlCachedConnection
from ..util.stComponents import showCodeSql
from ..util.stUtil import stripFields


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
