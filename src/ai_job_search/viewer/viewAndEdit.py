import pandas as pd
from pandas.core.frame import DataFrame
from ai_job_search.scrapper import glassdoorExtraInfo
from ai_job_search.viewer.util.viewUtil import (
    formatDetail, getValuesAsDict, mapDetailForm)
from ai_job_search.viewer.util.stUtil import (
    KEY_SELECTED_IDS, checkAndInput, checkAndPills, formatSql,
    getAndFilter, getBoolKeyName, getColumnTranslated, getSelectedRowsIds,
    getStateBool, getState, getStateBoolValue, initStates, pillsValuesToDict,
    setFieldValue, setState, sortFields)
from ai_job_search.viewer.viewAndEditConstants import (
    DB_FIELDS, DEFAULT_BOOL_FILTERS, DEFAULT_DAYS_OLD, DEFAULT_NOT_FILTERS,
    DEFAULT_ORDER,
    DEFAULT_SALARY_REGEX_FILTER, DEFAULT_SQL_FILTER, FF_KEY_BOOL_FIELDS,
    FF_KEY_BOOL_NOT_FIELDS, FF_KEY_DAYS_OLD, FF_KEY_ORDER, FF_KEY_SALARY,
    FF_KEY_SEARCH, FF_KEY_WHERE, FIELDS, FIELDS_BOOL, FIELDS_SORTED, HEIGHT,
    LIST_VISIBLE_COLUMNS, SEARCH_COLUMNS, SEARCH_INPUT_HELP, STYLE_JOBS_TABLE,
    VISIBLE_COLUMNS)
from tools.mysqlUtil import (
    MysqlUtil, QRY_SELECT_COUNT_JOBS, QRY_SELECT_JOBS_VIEWER, deleteJobsQuery,
    updateFieldsQuery)
import streamlit as st
from streamlit.column_config import CheckboxColumn
# from streamlit_js_eval import streamlit_js_eval


# TODO: Table scroll memory: when selecting a row below the visible scroll, a
#  rerun is fired and the table looses the scroll position
# TODO: Check jobs still exists by id

# @st.cache_resource
# def sqlConn():
#     return MysqlUtil()

def onTableChange():
    selected = getState('jobsListTable')
    if getState('singleSelect'):
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
            setState('preSelectedRows', value)
        else:
            setState('preSelectedRows', [0])
    setState('lastSelected', selected)


# https://docs.streamlit.io/develop/tutorials/elements/dataframe-row-selections
def table(df: DataFrame, fieldsSorted, visibleColumns):
    dfWithSelections = df.copy()
    preSelectedRows = getState('preSelectedRows', {})
    dfWithSelections.insert(0, "Sel", False)
    for row in preSelectedRows:
        if len(dfWithSelections.index) > row:
            rowIdx = dfWithSelections.index[row]
            dfWithSelections.loc[rowIdx, 'Sel'] = True
    # https://docs.streamlit.io/develop/api-reference/data/st.data_editor
    editedDf = st.data_editor(
        dfWithSelections,
        hide_index=True,
        # column_order=fieldSorted,
        on_change=onTableChange,
        column_config=getTableColsConfig(fieldsSorted, visibleColumns),
        height=HEIGHT,
        key='jobsListTable',
    )
    selectedRows = df[editedDf.Sel]
    setState('selectedRows', selectedRows)
    return selectedRows


def getTableColsConfig(fields, visibleColumns, selector=True):
    # https://docs.streamlit.io/develop/api-reference/data/st.column_config
    cfg = {}
    if selector:
        cfg["Sel"] = CheckboxColumn(required=True, width=25)
    cfg["0"] = None  # remove id from view, or set to 'id'
    # SORT VISIBLE COLUMNS FIRST
    for idx, c in enumerate(fields):
        if idx > 0 and c in visibleColumns:
            cfg[idx+2] = st.column_config.Column(
                label=getColumnTranslated(c), width='medium')
        else:
            cfg[idx+2] = None
    return cfg


def removeFiltersInNotFilters():
    if getStateBoolValue(FF_KEY_BOOL_FIELDS, FF_KEY_BOOL_NOT_FIELDS):
        values: list = getState(FF_KEY_BOOL_FIELDS)
        notValues: list = getState(FF_KEY_BOOL_NOT_FIELDS)
        # list comprehension
        notValues = [notVal for notVal in notValues if notVal not in values]
        return notValues
    return getState(FF_KEY_BOOL_NOT_FIELDS)


def getJobListQuery():
    filters = getState(FF_KEY_WHERE)
    where = '1=1'
    if getStateBool(FF_KEY_WHERE) and filters:
        where = f'({filters})'
    search = getState(FF_KEY_SEARCH)
    if search:
        searchArr = search.split(',')
        if len(searchArr) > 1:
            searchArr = '|'.join({f"{s.strip()}" for s in searchArr})
            searchFilter = f'rlike "({searchArr})"'
        else:
            searchFilter = f"like '%{search}%'"
        searchFilter = ' or '.join(
            {f'{col} {searchFilter}' for col in SEARCH_COLUMNS})
        where += f"\n and ({searchFilter})"
    salaryRegexFilter = getState(FF_KEY_SALARY)
    if getStateBool(FF_KEY_SALARY) and salaryRegexFilter:
        where += f'\n and salary rlike "{salaryRegexFilter}"'
    daysOldFilter = getState(FF_KEY_DAYS_OLD)
    if getStateBool(FF_KEY_DAYS_OLD) and daysOldFilter:
        where += '\n and DATE(created) >='
        where += f'     DATE_SUB(CURDATE(), INTERVAL {daysOldFilter} DAY)'
    if getStateBool(FF_KEY_BOOL_FIELDS):
        where += '\n' + getAndFilter(getState(FF_KEY_BOOL_FIELDS), True)
    if getStateBool(FF_KEY_BOOL_NOT_FIELDS):
        notValues = removeFiltersInNotFilters()
        where += '\n' + getAndFilter(notValues, False)
    params = {
        'selectFields': sortFields(DB_FIELDS, 'id,' + VISIBLE_COLUMNS),
        'where': where,
        'order': getState(FF_KEY_ORDER, DEFAULT_ORDER)
    }
    return QRY_SELECT_JOBS_VIEWER.format(**params)


def formFilter():
    formFilterByIdsSetup()
    with st.expander('Search filters'):
        with st.container():
            c1, c2, c3, c4 = st.columns([6, 1, 3, 3])
            with c1:
                c1.text_input(SEARCH_INPUT_HELP, '', key=FF_KEY_SEARCH)
            with c2:
                checkAndInput('Days old', FF_KEY_DAYS_OLD)
            with c3:
                checkAndInput("Salary regular expression", FF_KEY_SALARY)
            c4.text_input('Sort by columns', key=FF_KEY_ORDER)
            c1, c2 = st.columns(2)
            with c1:
                checkAndPills('Status filter', FIELDS_BOOL, FF_KEY_BOOL_FIELDS)
            with c2:
                checkAndPills('Status NOT filter', FIELDS_BOOL,
                              FF_KEY_BOOL_NOT_FIELDS)
            checkAndInput("SQL where filters", FF_KEY_WHERE)


def formFilterByIdsSetup():
    selectedIds = getState(KEY_SELECTED_IDS)
    if selectedIds and len(selectedIds) > 0:  # clean page entry point
        st.info(f'Selected ids: {selectedIds}')
        setState(getBoolKeyName(FF_KEY_BOOL_FIELDS), False)
        setState(getBoolKeyName(FF_KEY_BOOL_NOT_FIELDS), False)
        setState(FF_KEY_SEARCH, '')
        setState(getBoolKeyName(FF_KEY_SALARY), False)
        setState(getBoolKeyName(FF_KEY_DAYS_OLD), False)
        setState(getBoolKeyName(FF_KEY_WHERE), True)
        setState(FF_KEY_WHERE,
                 ' or '.join({f'id={id}' for id in selectedIds.split(',')}))
        setState(FF_KEY_ORDER, "company, title, created desc")
        setState(KEY_SELECTED_IDS, None)


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
        st.code(formatSql(query, False), 'sql')
        mysql = MysqlUtil()
        result = mysql.executeAndCommit(query, params)
        mysql.close()
        st.info(f'{result} row(s) updated.')
    else:
        st.info('Nothing to save.')


def detailForm(boolFieldsValues, comments, salary, company, client):
    with st.form('statusForm'):
        c1, c2 = st.columns([10, 1])
        with c1:
            st.pills('Status form', FIELDS_BOOL,
                     default=boolFieldsValues,
                     format_func=lambda c: getColumnTranslated(c),
                     selection_mode='multi',
                     label_visibility='collapsed',
                     key='statusFields')
        with c2:
            st.form_submit_button('Save', 'Save changes in job(s)',
                                  type='primary',
                                  on_click=detailFormSubmit)
        st.text_area("Comments", comments, key='comments')
        st.text_input("Salary", salary, key='salary')
        st.text_input("Company", company, key='company')
        st.text_input("Client", client, key='client')


def getCompanySalary(company, id):
    glassdoorExtraInfo.run(company, id)


def deleteSelectedRows():
    ids = getSelectedRowsIds('selectedRows')
    if len(ids) > 0:
        query = deleteJobsQuery(ids)
        st.code(query, 'sql')
        res = MysqlUtil().executeAndCommit(query)
        st.info(f'{res} job(s) deleted.  Ids: {ids}')


def view():
    # mysql = sqlConn()
    mysql = MysqlUtil()
    initStates({
        getBoolKeyName(FF_KEY_BOOL_FIELDS): True,
        FF_KEY_BOOL_FIELDS: DEFAULT_BOOL_FILTERS,
        getBoolKeyName(FF_KEY_BOOL_NOT_FIELDS): True,
        FF_KEY_BOOL_NOT_FIELDS: DEFAULT_NOT_FILTERS,
        FF_KEY_ORDER: DEFAULT_ORDER,
        getBoolKeyName(FF_KEY_SALARY): False,
        FF_KEY_SALARY: DEFAULT_SALARY_REGEX_FILTER,
        getBoolKeyName(FF_KEY_DAYS_OLD): True,
        FF_KEY_DAYS_OLD: DEFAULT_DAYS_OLD,
        getBoolKeyName(FF_KEY_WHERE): False,
        FF_KEY_WHERE: DEFAULT_SQL_FILTER
    })
    if getStateBool(FF_KEY_BOOL_FIELDS, FF_KEY_BOOL_NOT_FIELDS):
        res = removeFiltersInNotFilters()
        if res:
            setState(FF_KEY_BOOL_NOT_FIELDS, res)
    try:
        st.markdown(STYLE_JOBS_TABLE, unsafe_allow_html=True)
        formFilter()
        query = getJobListQuery()
        totalResults = mysql.count(QRY_SELECT_COUNT_JOBS)
        jobData = None
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("View generated sql"):
                # TODO: sqlparse.format(sql, reindent=True,
                #  keyword_case='upper')`
                st.code(formatSql(query, False), 'sql',
                        wrap_lines=True, line_numbers=True)
            df = pd.DataFrame(mysql.fetchAll(query), columns=FIELDS)
            filterResCnt = len(df.index)
            if filterResCnt > 0:
                selectedRows: DataFrame = table(
                    df, FIELDS_SORTED, LIST_VISIBLE_COLUMNS)
            else:
                st.warning('No results found for filter.')
                selectedRows = []
            totalSelected = len(selectedRows)
            if totalSelected == 1:
                selected = selectedRows.iloc[0]
                jobData = getValuesAsDict(selected, FIELDS_SORTED)
                (boolFieldsValues, comments, salary,
                 company, client) = mapDetailForm(jobData, FIELDS_BOOL)
            c1, c2, c3 = st.columns([14, 4, 3], vertical_alignment='center')
            c1.write(''.join([
                f'{filterResCnt}/{totalResults} filtered/total results,',
                f' {totalSelected} selected']))
            if totalSelected == 1:
                id = jobData['id']
                c2.button('Get company salary in Glassdoor',
                          on_click=getCompanySalary,
                          args=[company, id])
            c2.toggle('Single select', key='singleSelect')
            c3.button('Delete', 'deleteButton',
                      disabled=totalSelected < 1,
                      on_click=deleteSelectedRows,
                      type="primary")
            if totalSelected == 1:
                detailForm(boolFieldsValues, comments, salary, company, client)
        with col2:
            with st.container():
                if totalSelected > 1:
                    # FIXME: BAD SOLUTION, if fields order changed in query
                    config = {f: None for f in FIELDS} | {
                        'salary': 'Salary',
                        'required_technologies': 'Title',
                        'optional_technologies': 'Company',
                    }
                    st.dataframe(selectedRows,  # column_order=FIELDS,
                                 hide_index=True,
                                 use_container_width=True,
                                 column_config=config)
                    (boolFieldsValues, comments, salary,
                     company, client) = mapDetailForm(jobData, FIELDS_BOOL)
                    detailForm(boolFieldsValues, comments,
                               salary, company, client)
                if totalSelected == 1:
                    st.markdown(formatDetail(jobData))
                else:
                    st.warning("Select one job only to see job detail.")
    except InterruptedError as ex:
        mysql.close()
        raise ex
