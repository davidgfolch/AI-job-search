import re
import streamlit as st
from commonlib.mysqlUtil import MysqlUtil, deleteJobsQuery, updateFieldsQuery
from commonlib.sqlUtil import formatSql
from .streamlitConn import mysqlCachedConnection
from .util.stComponents import showCodeSql
from .util.stStateUtil import getState, setState
from .util.stUtil import getSelectedRowsIds, pillsValuesToDict, setFieldValue, setMessageInfo
from .viewAndEditConstants import (F_KEY_CLIENT, F_KEY_COMMENTS, F_KEY_COMPANY, F_KEY_SALARY, F_KEY_STATUS,
                                   FF_KEY_PRESELECTED_ROWS, FF_KEY_SINGLE_SELECT, FIELDS_BOOL)


def onTableChange():
    selected = getState('jobsListTable')
    if getState(FF_KEY_SINGLE_SELECT):
        lastSelected = getState('lastSelected')
        if lastSelected and selected and selected != lastSelected:
            lastSelectedRows = lastSelected['edited_rows']
            selectedRows = selected['edited_rows']
            last = set(lastSelectedRows)
            current = set(selectedRows)
            if len(current) == 1:
                value = current
            else:
                value = list(last ^ current)
            setState(FF_KEY_PRESELECTED_ROWS, list(value))
        else:
            setState(FF_KEY_PRESELECTED_ROWS, [0])
    setState('lastSelected', selected)


def markAs(boolField: str):
    ids = getSelectedRowsIds('selectedRows')
    if not ids or len(ids) < 1:
        return
    query, params = updateFieldsQuery(ids, {boolField: True})
    showCodeSql(formatSql(query, False))
    result = MysqlUtil(mysqlCachedConnection()).executeAndCommit(query, params)
    setMessageInfo(f'{result} row(s) marked as **{boolField.upper()}**.')


def deleteSelectedRows():
    ids = getSelectedRowsIds('selectedRows')
    if len(ids) > 0:
        query = deleteJobsQuery(ids)
        showCodeSql(query)
        res = MysqlUtil(mysqlCachedConnection()).executeAndCommit(query)
        st.info(f'{res} job(s) deleted.  Ids: {ids}')


def deleteSalary(id):
    MysqlUtil(mysqlCachedConnection()).executeAndCommit(f'update jobs set salary=null where id = {id}', {})


def formDetailSubmit():
    ids = getSelectedRowsIds('selectedRows')
    if not ids or len(ids) < 1:
        return
    fieldsValues = pillsValuesToDict(F_KEY_STATUS, FIELDS_BOOL)
    setFieldValue(fieldsValues, F_KEY_COMMENTS, None, len(ids) == 1)
    setFieldValue(fieldsValues, F_KEY_SALARY, None, len(ids) == 1)
    setFieldValue(fieldsValues, F_KEY_COMPANY, None, len(ids) == 1)
    setFieldValue(fieldsValues, F_KEY_CLIENT, None, len(ids) == 1)
    if fieldsValues:
        if len(ids) > 1:  # for several rows just fields not None or empty
            fieldsValues = {k: v for k, v in fieldsValues.items() if v}
        query, params = updateFieldsQuery(ids, keysToColumns(fieldsValues))
        showCodeSql(formatSql(query, False), params=params)
        result = MysqlUtil(mysqlCachedConnection()).executeAndCommit(query, params)
        setMessageInfo(f'{result} row(s) updated.')
    else:
        setMessageInfo('Nothing to save.')


def keysToColumns(fieldsValues: dict):
    """Renames streamlit form component keys to mysql columns"""
    return {re.sub(r'^form(.+)', r'\1', k): v for k, v in fieldsValues.items()}
