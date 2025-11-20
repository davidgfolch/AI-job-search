from pandas import DataFrame
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from commonlib.mysqlUtil import MysqlUtil
from commonlib.sqlUtil import deleteJobsQuery
from .cleanUtil import getIdsIndex
from ..mysqlConn import mysqlCachedConnection
from ..util.stComponents import showCodeSql
from ..util.stUtil import stripFields

DAYS = 15
DAYS2 = 25
COLUMNS = stripFields('Id,Title,Company,Created')


def getInfo():
    return f'Delete jobs (older than {DAYS} days not applied/flagged/seen)'


def getSelect():
    return f"""
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
    idsIdx = getIdsIndex(selectedRows)
    ids = list(selectedRows.iloc[row].iloc[idsIdx]
               for row in range(len(selectedRows)))
    query = deleteJobsQuery(ids)
    showCodeSql(query)
    count = MysqlUtil(mysqlCachedConnection()).executeAndCommit(query, {})
    st.info(f'Affected rows: {count}')
