import streamlit as st
from streamlit.column_config import CheckboxColumn
from pandas import DataFrame
from ai_job_search.tools.mysqlUtil import (
    QRY_SELECT_JOBS_VIEWER, binaryColumnIgnoreCase, getColumnTranslated)
from ai_job_search.tools.sqlUtil import getAndFilter
from ai_job_search.viewer.util.stStateUtil import (
    getStateBool, getStateBoolValue, setState)
from ai_job_search.viewer.util.stUtil import (
    KEY_SELECTED_IDS, checkAndInput, checkAndPills,
    getBoolKeyName, getState, scapeLatex)
from ai_job_search.viewer.util.viewUtil import fmtDetailOpField, formatDateTime
from ai_job_search.viewer.viewAndEditConstants import (
    COLUMNS_WIDTH, DEFAULT_ORDER, DETAIL_FORMAT, FF_KEY_BOOL_FIELDS,
    FF_KEY_BOOL_NOT_FIELDS, FF_KEY_COLUMNS_WIDTH, FF_KEY_DAYS_OLD,
    FF_KEY_LIST_HEIGHT, FF_KEY_ORDER, FF_KEY_PRESELECTED_ROWS, FF_KEY_SALARY,
    FF_KEY_SEARCH, FF_KEY_SINGLE_SELECT, FF_KEY_WHERE, FIELDS_BOOL, HEIGHT,
    SEARCH_COLUMNS, SEARCH_INPUT_HELP, VISIBLE_COLUMNS)
from ai_job_search.viewer.viewAndEditEvents import (
    deleteSalary, deleteSelectedRows, markAs, onTableChange)


def getJobListQuery():
    filters = getState(FF_KEY_WHERE)
    where = '1=1'
    if getStateBool(FF_KEY_WHERE) and filters:
        where = f'({filters})'
    if getState(getBoolKeyName(FF_KEY_SEARCH)):
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
        'selectFields': 'id,' + VISIBLE_COLUMNS,
        'where': where,
        'order': getState(FF_KEY_ORDER, DEFAULT_ORDER)
    }
    return QRY_SELECT_JOBS_VIEWER.format(**params)


def removeFiltersInNotFilters():
    if getStateBoolValue(FF_KEY_BOOL_FIELDS, FF_KEY_BOOL_NOT_FIELDS):
        values: list = getState(FF_KEY_BOOL_FIELDS)
        notValues: list = getState(FF_KEY_BOOL_NOT_FIELDS)
        # list comprehension
        notValues = [notVal for notVal in notValues if notVal not in values]
        return notValues
    return getState(FF_KEY_BOOL_NOT_FIELDS)


# https://docs.streamlit.io/develop/tutorials/elements/dataframe-row-selections
def table(df: DataFrame, fieldsSorted, visibleColumns) -> DataFrame:
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
                # TODO: configurable columns width
                label=getColumnTranslated(c), width='medium')
        else:
            cfg[idx+2] = None
    return cfg


def detailForSingleSelection():
    st.divider()
    c1, c2, _ = st.columns([4, 3, 30])
    c1.button('Ignore', help='Mark as ignored and Save',
              key='ignore2', kwargs={'boolField': 'ignored'},
              on_click=markAs)
    c2.button('Seen', help='Mark as Seen and Save',
              key='seen2', kwargs={'boolField': 'seen'},
              on_click=markAs)


def formFilter():
    if getStateBool(FF_KEY_BOOL_FIELDS, FF_KEY_BOOL_NOT_FIELDS):
        if res := removeFiltersInNotFilters():
            setState(FF_KEY_BOOL_NOT_FIELDS, res)
    formFilterByIdsSetup()
    with st.expander('Search filters'):
        with st.container():
            c1, c2, c3, c4 = st.columns([6, 1, 3, 3])
            with c1:
                checkAndInput(SEARCH_INPUT_HELP, FF_KEY_SEARCH,
                              withContainer=False, withHistory=True)
            with c2:
                checkAndInput('Days old', FF_KEY_DAYS_OLD,
                              withContainer=False)
            with c3:
                checkAndInput("Salary regular expression", FF_KEY_SALARY,
                              withContainer=False, withHistory=True)
            with c4:
                checkAndInput('Sort by columns', FF_KEY_ORDER,
                              withContainer=False, withHistory=True)
            c1, c2 = st.columns(2)
            with c1:
                checkAndPills('Status filter', FIELDS_BOOL, FF_KEY_BOOL_FIELDS)
            with c2:
                checkAndPills('Status NOT filter', FIELDS_BOOL,
                              FF_KEY_BOOL_NOT_FIELDS)
            checkAndInput("SQL where filters", FF_KEY_WHERE,
                          withContainer=False, withHistory=True)


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
        setState(FF_KEY_ORDER, "modified desc")
        setState(KEY_SELECTED_IDS, None)


def tableFooter(totalResults, filterResCnt, totalSelected):
    totals = f'<p style="text-align:right">{totalSelected} ' + \
        f'selected ({filterResCnt} filtered, ' + \
        f'{totalResults} total)</p>'
    st.write(totals, unsafe_allow_html=True)
    if filterResCnt > 0:
        c = st.columns([3, 3, 3, 1, 5, 5, 5], vertical_alignment='center')
        c[0].button('Ignore', help='Mark as ignored and Save',
                    kwargs={'boolField': 'ignored'}, on_click=markAs)
        c[1].button('Seen', help='Mark as Seen and Save',
                    kwargs={'boolField': 'seen'}, on_click=markAs)
        c[2].button('Delete', 'deleteButton', help='Delete selected job(s)',
                    disabled=totalSelected < 1,
                    on_click=deleteSelectedRows, type="primary")
        c[3].write('|')
        c[4].toggle('Single select', key=FF_KEY_SINGLE_SELECT)
        c[5].number_input('Heigh', key=FF_KEY_LIST_HEIGHT,
                          step=100, label_visibility='collapsed')
        c[6].number_input('Columns width', key=FF_KEY_COLUMNS_WIDTH,
                          value=COLUMNS_WIDTH, step=0.1,
                          label_visibility='collapsed')


def formatDetail(jobData: dict):
    data = scapeLatex(jobData, ['markdown', 'title'])
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
