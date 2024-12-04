import re
import pandas as pd
from pandas.core.frame import DataFrame
from ai_job_search.viewer.viewUtil import (formatSql, mapDetailForm)
from viewer.stUtil import (
    KEY_SELECTED_IDS, checkAndInput,
    getAndFilter, getSelectedRowsIds, getStateOrDefault, initStates,
    pillsValuesToDict, scapeLatex, setFieldValue, setState,
    sortFields, stripFields)
from tools.mysqlUtil import (
    MysqlUtil, QRY_SELECT_COUNT_JOBS, QRY_SELECT_JOBS_VIEWER, deleteJobsQuery,
    updateFieldsQuery)
import streamlit as st
from streamlit.column_config import CheckboxColumn
# from streamlit_js_eval import streamlit_js_eval


# TODO: Table scroll memory: when selecting a row below the visible scroll, a rerun is fired and the table looses the scroll position
# TODO: Check jobs still exists by id

HEIGHT = 300

# @st.cache_resource
# def sqlConn():
#     return MysqlUtil()


# COLUMNS (MYSQL & DATAFRAME)
VISIBLE_COLUMNS = """
salary,title,company,client,required_technologies,created"""
DB_FIELDS_BOOL = """flagged,`like`,ignored,seen,applied,discarded,closed,
interview_rh,interview,interview_tech,interview_technical_test,interview_technical_test_done,
ai_enriched,relocation,easyApply"""
DB_FIELDS = f"""id,salary,title,required_technologies,optional_technologies,
company,client,markdown,business_sector,required_languages,location,url,created,
comments,{DB_FIELDS_BOOL}"""
DB_FIELDS_MERGE = """salary,required_technologies,optional_technologies,
company,client,business_sector,required_languages,comments"""
# FILTERS
RLIKE = '(java[^script]|python|scala|clojure)'
DEFAULT_SQL_FILTER = f"""
required_technologies rlike '{RLIKE}'
 or title rlike '{RLIKE}'
 or markdown rlike '{RLIKE}'"""
DEFAULT_SALARY_REGEX_FILTER = "([€$] *[0-9]{2,}|[0-9]{2,} *[€$])"
DEFAULT_ORDER = "created desc"
# DETAIL FORMAT
DETAIL_FORMAT = """
## [{title}]({url})

- Company: `{company}`
- Client: `{client}`
- Salary: `{salary}`
- Skills
  - Required: `{required_technologies}`
  - Optional: `{optional_technologies}`

`{created}` - `{createdTime}`

{markdown}
"""

LIST_VISIBLE_COLUMNS = stripFields(VISIBLE_COLUMNS)
FIELDS = stripFields(DB_FIELDS)
FIELDS_BOOL = stripFields(DB_FIELDS_BOOL)
FIELDS_MERGE = stripFields(DB_FIELDS_MERGE)
FIELDS_SORTED = sortFields(DB_FIELDS, 'id,' + VISIBLE_COLUMNS).split(',')
DEFAULT_NOT_FILTERS = stripFields('seen,ignored,applied,discarded,closed')


SEARCH_COLUMNS = ['title', 'company', 'client', 'markdown']
SEARCH_INPUT_HELP = f"""
Enter search concepts (for {','.join(SEARCH_COLUMNS)})  separated by commas
 (note text between commas are mysql regex)"""


STYLE_JOBS_TABLE = """
    <style>
        .st-key-jobsListTable .stDataFrame > *,
        .st-key-jobsListTable .stDataFrame > div > * {
            background-color: darkcyan;
        }
    </style>
    """


def onTableChange():
    selected = getStateOrDefault('jobsListTable')
    if getStateOrDefault('singleSelect'):
        lastSelected = getStateOrDefault('lastSelected')
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
    setState('lastSelected', selected)


# https://docs.streamlit.io/develop/tutorials/elements/dataframe-row-selections
def table(df: DataFrame, fieldsSorted, visibleColumns):
    dfWithSelections = df.copy()
    preSelectedRows = getStateOrDefault('preSelectedRows', {})
    dfWithSelections.insert(0, "Sel", False)
    for row in preSelectedRows:
        try:
            rowIdx = dfWithSelections.index[row]
        except IndexError:
            # Fails when some previously selected row are deleted
            pass
        if rowIdx and rowIdx < len(dfWithSelections):
            dfWithSelections.loc[dfWithSelections.index[row], 'Sel'] = True
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


def getValuesAsDict(series):
    res = {}
    for idx, f in enumerate(FIELDS_SORTED):
        value = series.iloc[idx]
        if f == 'markdown' or f == 'comments':
            res[f] = value.decode('utf-8') if value else value
        else:
            res[f] = value.strip() if isinstance(value, str) else value
    return res


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


def getColumnTranslated(c):
    return re.sub(r'[_-]', ' ', c)


def getJobListQuery(salary, search, filters, boolFilters,
                    boolNotFilters, order):
    isSalaryFilter, salaryRegexFilter = salary
    isWhereFilter, filters = filters
    where = f'({filters})' if isWhereFilter and filters else '1=1'
    if search:
        searchArr = search.split(',')
        if len(searchArr) > 1:
            searchArr = '|'.join({f"{s.strip()}" for s in searchArr})
            searchFilter = f'rlike "({searchArr})"'
        else:
            searchFilter = f"like '%{search}%'"
        searchFilter = ' or '.join(
            {f'{col} {searchFilter}' for col in SEARCH_COLUMNS})
        where += f" and ({searchFilter})"
    where += getAndFilter(boolFilters, True)
    where += getAndFilter(boolNotFilters, False)
    if isSalaryFilter & len(salaryRegexFilter.strip()) > 0:
        where += f' and salary rlike "{salaryRegexFilter}"'
    params = {
        'selectFields': sortFields(DB_FIELDS, 'id,' + VISIBLE_COLUMNS),
        'where': where,
        'order': DEFAULT_ORDER if not order else order
    }
    return QRY_SELECT_JOBS_VIEWER.format(**params)


def formFilter():
    formFilterByIdsSetup()
    with st.expander('Search filters'):
        with st.container(border=1):
            boolFilters = st.pills('Status filter', FIELDS_BOOL,
                                   selection_mode='multi',
                                   key='boolFieldsFilter')
            boolNotFilters = st.pills('Status NOT filter', FIELDS_BOOL,
                                      selection_mode='multi',
                                      default=DEFAULT_NOT_FILTERS,
                                      key='boolFieldsNotFilter')
            col1, col2 = st.columns(2)
            with col1:
                search = st.text_input(
                    SEARCH_INPUT_HELP, '', key='searchFilter')
            with col2:
                salary = checkAndInput("Salary regular expression",
                                       'isSalFilter', 'salaryFilter')
            filters = checkAndInput("SQL where filters",
                                    'isWhereFilter', 'whereFilter')
            order = st.text_input('Sort by columns', key='selectOrder')
    return salary, search, filters, boolFilters, boolNotFilters, order


def formFilterByIdsSetup():
    selectedIds = getStateOrDefault(KEY_SELECTED_IDS)
    if selectedIds and len(selectedIds) > 0:  # clean page entry point
        st.info(f'Selected ids: {selectedIds}')
        setState('boolFieldsFilter', [])
        setState('boolFieldsNotFilter', [])
        setState('searchFilter', '')
        setState('isSalFilter', False)
        setState('isWhereFilter', True)
        setState('whereFilter',
                 ' or '.join({f'id={id}' for id in selectedIds.split(',')}))
        setState('selectOrder', "company, title, created desc")
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
        st.code(formatSql(query), 'sql')
        mysql = MysqlUtil()
        result = mysql.executeAndCommit(query, params)
        mysql.close()
        st.info(f'{result} row(s) updated.')
    else:
        st.info('Nothing to save.')


def detailForm(jobData):
    (boolFieldsValues, comments,
     salary, company, client) = mapDetailForm(jobData, FIELDS_BOOL)
    with st.form('statusForm'):
        c1, c2 = st.columns([10, 1])
        with c1:
            st.pills('Status form', FIELDS_BOOL,
                     selection_mode='multi',
                     default=boolFieldsValues,
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
        'isSalFilter': True,
        'isWhereFilter': True,
        'selectOrder': DEFAULT_ORDER,
        'salaryFilter': DEFAULT_SALARY_REGEX_FILTER,
        'whereFilter': DEFAULT_SQL_FILTER
    })
    try:
        st.markdown(STYLE_JOBS_TABLE, unsafe_allow_html=True)
        (salary, search, filters, boolFilters,
         boolNotFilters, order) = formFilter()
        query = getJobListQuery(salary, search, filters,
                                boolFilters, boolNotFilters, order)
        totalResults = mysql.count(QRY_SELECT_COUNT_JOBS)
        jobData = None
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("View generated sql"):
                st.code(formatSql(query), 'sql',
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
            c1, c2, c3 = st.columns([14, 4, 3], vertical_alignment='center')
            c1.write(''.join([
                f'{filterResCnt}/{totalResults} filtered/total results,',
                f' {totalSelected} selected']))
            c2.toggle('Single select', key='singleSelect')
            c3.button('Delete', 'deleteButton',
                      disabled=totalSelected < 1,
                      on_click=deleteSelectedRows,
                      type="primary")
            if totalSelected == 1:
                selected = selectedRows.iloc[0]
                jobData = getValuesAsDict(selected)
                detailForm(jobData)
        with col2:
            with st.container():
                if totalSelected > 1:
                    # FIXME: BAD SOLUTION, if fields changed
                    config = {f: None for f in FIELDS}
                    config['salary'] = 'Salary'
                    config['required_technologies'] = 'Title'
                    config['optional_technologies'] = 'Company'
                    st.dataframe(selectedRows,  # column_order=FIELDS,
                                 hide_index=True,
                                 use_container_width=True,
                                 column_config=config)
                    detailForm(jobData)
                if totalSelected == 1:
                    data = scapeLatex(jobData)
                    data['createdTime'] = data['created'].time()
                    data['created'] = data['created'].date()
                    st.markdown(DETAIL_FORMAT.format(**data))
                else:
                    st.warning("Select one job only to see job detail.")
    except InterruptedError as ex:
        mysql.close()
        raise ex
