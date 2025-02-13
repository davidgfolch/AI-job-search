import streamlit as st
from ai_job_search.tools.mysqlUtil import (
    MysqlUtil, deleteJobsQuery, updateFieldsQuery)
from ai_job_search.viewer.util.stUtil import (
    formatSql, getSelectedRowsIds, getState, pillsValuesToDict, setFieldValue,
    setMessageInfo, setState, showCodeSql)
from ai_job_search.viewer.viewAndEditConstants import (
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
            setState(FF_KEY_PRESELECTED_ROWS, value)
        else:
            setState(FF_KEY_PRESELECTED_ROWS, [0])
    setState('lastSelected', selected)


def markAs(boolField: str):
    ids = getSelectedRowsIds('selectedRows')
    if not ids or len(ids) < 1:
        return
    query, params = updateFieldsQuery(ids, {boolField: True})
    showCodeSql(formatSql(query, False))
    with MysqlUtil() as _:
        result = _.executeAndCommit(query, params)
    setMessageInfo(f'{result} row(s) marked as **{boolField.upper()}**.')


def deleteSelectedRows():
    ids = getSelectedRowsIds('selectedRows')
    if len(ids) > 0:
        query = deleteJobsQuery(ids)
        showCodeSql(query)
        with MysqlUtil() as _:
            res = _.executeAndCommit(query)
        st.info(f'{res} job(s) deleted.  Ids: {ids}')


def deleteSalary(id):
    with MysqlUtil() as _:
        _.executeAndCommit(f'update jobs set salary=null where id = {id}', {})


def detailFormSubmit():
    ids = getSelectedRowsIds('selectedRows')
    if not ids or len(ids) < 1:
        return
    fieldsValues = pillsValuesToDict('statusFields', FIELDS_BOOL)
    setFieldValue(fieldsValues, 'comments', None, len(ids) == 1)
    setFieldValue(fieldsValues, 'salary', None, len(ids) == 1)
    setFieldValue(fieldsValues, 'company', None, len(ids) == 1)
    setFieldValue(fieldsValues, 'client', None, len(ids) == 1)
    if fieldsValues:
        if len(ids) > 1:  # for several rows just fields not None or empty
            fieldsValues = {k: v for k, v in fieldsValues.items() if v}
        query, params = updateFieldsQuery(ids, fieldsValues)
        showCodeSql(formatSql(query, False))
        with MysqlUtil() as _:
            result = _.executeAndCommit(query, params)
        setMessageInfo(f'{result} row(s) updated.')
    else:
        setMessageInfo('Nothing to save.')
