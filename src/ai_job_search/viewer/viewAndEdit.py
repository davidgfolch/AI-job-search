import pandas as pd
from pandas.core.frame import DataFrame
from ai_job_search.tools.util import SHOW_SQL
from ai_job_search.viewer.util.viewUtil import (
    fmtDetailOpField, formatDateTime, getValuesAsDict, gotoPageByUrl,
    mapDetailForm)
from ai_job_search.viewer.util.stUtil import (
    KEY_SELECTED_IDS, PAGE_VIEW_IDX, checkAndInput,
    checkAndPills, formatSql,
    getAndFilter, getBoolKeyName, getColumnTranslated, getSelectedRowsIds,
    getStateBool, getState, getStateBoolValue, initStates, pillsValuesToDict,
    scapeLatex, setFieldValue, setMessageInfo, setState, showCodeSql,
    sortFields)
from ai_job_search.viewer.viewAndEditConstants import (
    COLUMNS_WIDTH, DB_FIELDS, DEFAULT_BOOL_FILTERS, DEFAULT_DAYS_OLD,
    DEFAULT_NOT_FILTERS, DEFAULT_ORDER,
    DEFAULT_SALARY_REGEX_FILTER, DEFAULT_SQL_FILTER, DETAIL_FORMAT,
    FF_KEY_BOOL_FIELDS, FF_KEY_BOOL_NOT_FIELDS, FF_KEY_COLUMNS_WIDTH,
    FF_KEY_DAYS_OLD, FF_KEY_LIST_HEIGHT, FF_KEY_ORDER, FF_KEY_PRESELECTED_ROWS,
    FF_KEY_SALARY, FF_KEY_SEARCH, FF_KEY_SINGLE_SELECT, FF_KEY_WHERE, FIELDS,
    FIELDS_BOOL, FIELDS_SORTED, HEIGHT, LIST_VISIBLE_COLUMNS, SEARCH_COLUMNS,
    SEARCH_INPUT_HELP, STYLE_JOBS_TABLE, VISIBLE_COLUMNS)
from tools.mysqlUtil import (
    SELECT_APPLIED_JOB_IDS_BY_COMPANY,
    SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT, MysqlUtil, QRY_SELECT_COUNT_JOBS,
    QRY_SELECT_JOBS_VIEWER,
    binaryColumnIgnoreCase, deleteJobsQuery, updateFieldsQuery)
import streamlit as st
from streamlit.column_config import CheckboxColumn
# from streamlit_js_eval import streamlit_js_eval


# TODO: Table scroll memory: when selecting a row below the visible scroll, a
#  rerun is fired and the table looses the scroll position
# TODO: Check jobs still exists by id

# @st.cache_resource
# def sqlConn():
#     return MysqlUtil()


mysql = None


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


# https://docs.streamlit.io/develop/tutorials/elements/dataframe-row-selections
def table(df: DataFrame, fieldsSorted, visibleColumns):
    dfWithSelections = df.copy()
    preSelectedRows = getState(FF_KEY_PRESELECTED_ROWS, [])
    dfWithSelections.insert(0, "Sel", False)
    for row in preSelectedRows:
        row = int(row)
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
        use_container_width=True,
        height=getState(FF_KEY_LIST_HEIGHT, HEIGHT),
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
            searchFilter = f'rlike "({searchArr.lower()})"'
        else:
            searchFilter = f"like '%{search.lower()}%'"
        searchFilter = ' or '.join(
            {f'{binaryColumnIgnoreCase(col)} {searchFilter}'
             for col in SEARCH_COLUMNS})
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
                checkAndInput('Days old', FF_KEY_DAYS_OLD, withContainer=False)
            with c3:
                checkAndInput("Salary regular expression",
                              FF_KEY_SALARY, withContainer=False)
            c4.text_input('Sort by columns', key=FF_KEY_ORDER)
            c1, c2 = st.columns(2)
            with c1:
                checkAndPills('Status filter', FIELDS_BOOL, FF_KEY_BOOL_FIELDS)
            with c2:
                checkAndPills('Status NOT filter', FIELDS_BOOL,
                              FF_KEY_BOOL_NOT_FIELDS)
            checkAndInput("SQL where filters", FF_KEY_WHERE, [10, 90], False)


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
        showCodeSql(formatSql(query, False))
        mysql = MysqlUtil()
        result = mysql.executeAndCommit(query, params)
        mysql.close()
        setMessageInfo(f'{result} row(s) updated.')
    else:
        setMessageInfo('Nothing to save.')


def markAs(boolField: str):
    ids = getSelectedRowsIds('selectedRows')
    if not ids or len(ids) < 1:
        return
    query, params = updateFieldsQuery(ids, {boolField: True})
    showCodeSql(formatSql(query, False))
    mysql = MysqlUtil()
    result = mysql.executeAndCommit(query, params)
    mysql.close()
    setMessageInfo(f'{result} row(s) marked as **{boolField.upper()}**.')


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
        rows = 5 if comments is None else len(comments.split('\n'))
        rows = rows if rows > 4 else 5
        st.text_area("Comments", comments, key='comments', height=rows*20)
        st.text_input("Salary", salary, key='salary')
        st.text_input("Company", company, key='company')
        st.text_input("Client", client, key='client')


def deleteSelectedRows():
    ids = getSelectedRowsIds('selectedRows')
    if len(ids) > 0:
        query = deleteJobsQuery(ids)
        showCodeSql(query)
        res = MysqlUtil().executeAndCommit(query)
        st.info(f'{res} job(s) deleted.  Ids: {ids}')


def view():
    global mysql
    mysql = MysqlUtil()
    initStates({
        FF_KEY_SEARCH: '',
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
        FF_KEY_WHERE: DEFAULT_SQL_FILTER,
        FF_KEY_SINGLE_SELECT: True,
        FF_KEY_LIST_HEIGHT: HEIGHT
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
        columnsWidth = getState(FF_KEY_COLUMNS_WIDTH, 0.5)
        col1, col2 = st.columns([columnsWidth, 1-columnsWidth])
        with col1:
            if SHOW_SQL:
                with st.expander("View generated sql"):
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
            st.write(''.join([
                f'{totalSelected} selected ',
                f'({filterResCnt} filtered, ',
                f'{totalResults} total)',
            ]))
            c = st.columns([3, 3, 3, 1, 5, 5, 5],
                           vertical_alignment='center')
            c[0].button('Ignore',
                        help='Mark as ignored and Save',
                        kwargs={'boolField': 'ignored'},
                        on_click=markAs)
            c[1].button('Seen',
                        help='Mark as Seen and Save',
                        kwargs={'boolField': 'seen'},
                        on_click=markAs)
            c[2].button('Delete', 'deleteButton',
                        help='Delete selected job(s)',
                        disabled=totalSelected < 1,
                        on_click=deleteSelectedRows,
                        type="primary")
            c[3].write('|')
            c[4].toggle('Single select', key=FF_KEY_SINGLE_SELECT)
            c[5].number_input('Heigh', key=FF_KEY_LIST_HEIGHT,
                              value=HEIGHT, step=100,
                              label_visibility='collapsed', )
            c[6].number_input('Columns width', key=FF_KEY_COLUMNS_WIDTH,
                              value=COLUMNS_WIDTH, step=0.1,
                              label_visibility='collapsed', )
            if totalSelected == 1:
                detailForm(boolFieldsValues, comments, salary, company, client)
        with col2:
            with st.container():
                if totalSelected > 1:
                    # Table shown on the right when more than 1 is selected
                    # FIXME: BAD SOLUTION, if fields order changed in query
                    # check DB_FIELDS
                    config = {f: None for f in FIELDS} | {
                        'salary': 'Salary',
                        'title': 'Title',
                        'required_technologies': 'Company',
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
                    addCompanyAppliedJobsInfo(jobData)
                    formatDetail(jobData)
                    st.divider()
                    c1, c2, _ = st.columns([4, 3, 30])
                    c1.button('Ignore',
                              help='Mark as ignored and Save',
                              key='ignore2',
                              kwargs={'boolField': 'ignored'},
                              on_click=markAs)
                    c2.button('Seen',
                              help='Mark as Seen and Save',
                              key='seen2',
                              kwargs={'boolField': 'seen'},
                              on_click=markAs)
                else:
                    st.warning("Select one job only to see job detail.")
    except InterruptedError as ex:
        mysql.close()
        raise ex


def addCompanyAppliedJobsInfo(jobData):
    params = {'company': str(jobData['company']).lower(),
              'id':  str(jobData['id'])}
    query = SELECT_APPLIED_JOB_IDS_BY_COMPANY
    # For Joppy offers check also client
    # (client should be manually set by the user)
    company = jobData['company']
    if params['company'] == 'joppy' and jobData['client']:
        query += SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT
        client = str(jobData['client']).lower()
        params |= {'client': client}
        company = jobData['client']
    rows = mysql.fetchAll(query.format(**params))
    ids = ','.join([str(r[0]) for r in rows])
    if len(ids) > 0:
        jobData['company'] += ' ' + gotoPageByUrl(
            PAGE_VIEW_IDX,
            f':point_right: :warning: already applied {company} ({ids})',
            ids)


def formatDetail(jobData: dict):
    data = scapeLatex(jobData, 'markdown')
    formatDateTime(jobData)
    data = {k: (data[k] if data[k] else None)
            for k in data.keys()}
    str = DETAIL_FORMAT.format(**data)
    str += fmtDetailOpField(data, 'client')
    reqSkills = fmtDetailOpField(data, 'required_technologies', 'Required', 2)
    opSkills = fmtDetailOpField(data, 'optional_technologies', 'Optional', 2)
    if reqSkills + opSkills != '':
        str += ''.join(["- Skills\n", reqSkills, opSkills])
    st.markdown(str, unsafe_allow_html=True)
    salary = fmtDetailOpField(data, 'salary')
    if salary != '':
        c1, c2 = st.columns(2)
        c1.write(salary)
        c2.button('', icon='🗑️',
                  on_click=deleteSalary, kwargs={'id': jobData['id']})
    if val := data.get('comments'):
        with st.expander('Comments', expanded=True):
            st.markdown(val)
    st.markdown(data['markdown'])


def deleteSalary(id):
    mysql.executeAndCommit(f'update jobs set salary=null where id = {id}', {})
