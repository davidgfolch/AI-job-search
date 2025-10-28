import re
from typing import Dict
import streamlit as st
from pandas import DataFrame
from mysql.connector.types import RowItemType
from commonlib.sqlUtil import formatSql
from commonlib.util import getEnv
from commonlib.mysqlUtil import (SELECT_APPLIED_JOB_IDS_BY_COMPANY, SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT, QRY_SELECT_COUNT_JOBS, SELECT_APPLIED_JOB_ORDER_BY,
                                 MysqlUtil, getColumnTranslated)
from viewer.streamlitConn import mysqlCachedConnection
from viewer.util.stComponents import showCodeSql
from viewer.util.stStateUtil import getBoolKeyName, getState, initStates
from viewer.util.viewUtil import fmtDetailOpField, formatDateTime, getValueAsDict, gotoPageByUrl, mapDetailForm
from viewer.util.stUtil import getTextAreaHeightByText, inColumns, scapeLatex, stripFields
from viewer.viewAndEditConstants import (
    DB_FIELDS, DEFAULT_BOOL_FILTERS, DEFAULT_DAYS_OLD, DEFAULT_NOT_FILTERS, DEFAULT_ORDER, DEFAULT_SQL_FILTER, DETAIL_FORMAT,
    F_KEY_CLIENT, F_KEY_COMMENTS, F_KEY_COMPANY, F_KEY_SALARY, F_KEY_STATUS, FF_KEY_BOOL_FIELDS, FF_KEY_BOOL_NOT_FIELDS,
    FF_KEY_COLUMNS_WIDTH, FF_KEY_CONFIG_PILLS, FF_KEY_DAYS_OLD, FF_KEY_LIST_HEIGHT, FF_KEY_ORDER, FF_KEY_SALARY, FF_KEY_SEARCH,
    FF_KEY_SINGLE_SELECT, FF_KEY_WHERE, FIELDS, FIELDS_BOOL, FIELDS_SORTED, LIST_HEIGHT, LIST_VISIBLE_COLUMNS, STYLE_JOBS_TABLE)
from viewer.viewAndEditEvents import deleteSalary, salaryCalculator, formDetailSubmit
from viewer.viewAndEditHelper import detailForSingleSelection, formFilter, getJobListQuery, table, tableFooter
from viewer.viewConstants import PAGE_VIEW_IDX


# from streamlit_js_eval import streamlit_js_eval
# TODO: Table scroll memory: when selecting a row below the visible scroll, a
#  rerun is fired and the table looses the scroll position
# TODO: Check jobs still exists by id


def view():
    global mysql
    mysql = MysqlUtil(mysqlCachedConnection())
    initStates({
        FF_KEY_SEARCH: '',
        getBoolKeyName(FF_KEY_BOOL_FIELDS): True,
        FF_KEY_BOOL_FIELDS: DEFAULT_BOOL_FILTERS,
        getBoolKeyName(FF_KEY_BOOL_NOT_FIELDS): True,
        FF_KEY_BOOL_NOT_FIELDS: DEFAULT_NOT_FILTERS,
        FF_KEY_ORDER: DEFAULT_ORDER,
        getBoolKeyName(FF_KEY_SALARY): False,
        FF_KEY_SALARY: getEnv('SALARY_FILTER_REGEX'),
        getBoolKeyName(FF_KEY_DAYS_OLD): True,
        FF_KEY_DAYS_OLD: DEFAULT_DAYS_OLD,
        getBoolKeyName(FF_KEY_WHERE): False,
        FF_KEY_WHERE: DEFAULT_SQL_FILTER,
        FF_KEY_SINGLE_SELECT: True,
        FF_KEY_LIST_HEIGHT: LIST_HEIGHT
    })
    st.markdown(STYLE_JOBS_TABLE, unsafe_allow_html=True)
    formFilter()
    jobData: Dict = {}
    columnsWidth: float = getState(FF_KEY_COLUMNS_WIDTH, 0.5)
    col1, col2 = st.columns([columnsWidth, 1-columnsWidth])
    with col1:
        filterResCnt, selectedRows, totalSelected = tableView()
        totalResults = mysql.count(QRY_SELECT_COUNT_JOBS)
        tableFooter(totalResults, filterResCnt, totalSelected, selectedRows)
        if totalSelected == 1:
            jobData = getJobData(selectedRows)
            formDetail(jobData)
    with col2:
        with st.container():
            if totalSelected > 1:
                formDetailForMultipleSelection(selectedRows, jobData)
            elif totalSelected == 1:
                addCompanyAppliedJobsInfo(jobData)
                showDetail(jobData)
                detailForSingleSelection()
            elif filterResCnt > 0:
                st.warning("Select one job only to see job detail.")


def formDetail(jobData):
    boolFieldsValues, comments, salary, company, client = mapDetailForm(jobData, FIELDS_BOOL)
    with st.form('statusForm'):
        inColumns([(10, lambda _: st.pills('Status form', FIELDS_BOOL,
                                           default=boolFieldsValues,
                                           format_func=lambda c: getColumnTranslated(c),
                                           selection_mode='multi',
                                           label_visibility='collapsed',
                                           key=F_KEY_STATUS)),
                   (1, lambda _: st.form_submit_button('Save', 'Save changes in job(s)',
                                                       type='primary',
                                                       on_click=formDetailSubmit))])
        st.text_area("Comments", comments, key=F_KEY_COMMENTS, height=getTextAreaHeightByText(comments))
        st.text_input("Salary", salary, key=F_KEY_SALARY)
        st.text_input("Company", company, key=F_KEY_COMPANY)
        st.text_input("Client", client, key=F_KEY_CLIENT)


def getJobData(selectedRows: DataFrame) -> Dict:
    selected = selectedRows.iloc[0]
    id = int(selected.iloc[0])
    jobData: Dict[str, RowItemType] = mysql.fetchOne(f"select {DB_FIELDS} from jobs where id=%s", id)
    fieldsArr = stripFields(DB_FIELDS)
    return {
        f'{fieldsArr[idx]}': getValueAsDict(fieldsArr[idx], data)
        for idx, data in enumerate(jobData)
    }


def tableView():
    query = getJobListQuery()
    if 'showSql' in getState(FF_KEY_CONFIG_PILLS, []):
        with st.expander("View generated sql"):
            st.code(formatSql(query, False), 'sql',
                    wrap_lines=True, line_numbers=True)
    try:
        res = mysql.fetchAll(query)
    except Exception as e:
        showCodeSql(query, showSql=True)
        raise e
    df = DataFrame(res, columns=['id'] + LIST_VISIBLE_COLUMNS)
    filterResCnt = len(df.index)
    if filterResCnt > 0:
        selectedRows = table(df, FIELDS_SORTED, LIST_VISIBLE_COLUMNS)
        # selectedRows = tableV2(df, FIELDS_SORTED, LIST_VISIBLE_COLUMNS)
    else:
        st.warning('No results found for filter.')
        selectedRows = DataFrame()
    totalSelected = len(selectedRows)
    return filterResCnt, selectedRows, totalSelected


def showDetail(jobData: dict):
    data: Dict = scapeLatex(jobData, ['markdown', 'title'])
    formatDateTime(data)
    data = {k: (data[k] if data[k] else None) for k in data.keys()}
    outStr = DETAIL_FORMAT.format(**data)
    outStr += fmtDetailOpField(data, 'client')
    reqSkills = fmtDetailOpField(data, 'required_technologies', 'Required', 2)
    opSkills = fmtDetailOpField(data, 'optional_technologies', 'Optional', 2)
    if reqSkills + opSkills != '':
        outStr += ''.join(["- Skills\n", reqSkills, opSkills])
    if error := jobData.get('ai_enrich_error', None):
        outStr += f'- :red[AI enrich error:] {error}'
    st.markdown(outStr, unsafe_allow_html=True)
    salary = fmtDetailOpField(data, 'salary')
    if salary != '':
        inColumns([
            (10, lambda _: st.write(salary)),
            (1, lambda _: st.button('', icon='🧮', key='calculatorButton', on_click=salaryCalculator, kwargs={'salary': jobData['salary']})),
            (1, lambda _: st.button('', icon='🗑️', key='trashButton', on_click=deleteSalary, kwargs={'id': jobData['id']})),
        ])
    cvMatchPercentage = fmtDetailOpField(data, 'cv_match_percentage', 'CV match', 2)
    if cvMatchPercentage != '':
        with st.expander(cvMatchPercentage+'%', expanded=True):
            if data['cv_match_percentage'] > -1:
                st.progress(data['cv_match_percentage'])
            else:
                st.write('AI CV Match error')
    if val := data.get('comments'):
        with st.expander('Comments', expanded=True):
            st.markdown(val)
    st.markdown(data['markdown'])


def formDetailForMultipleSelection(selectedRows, jobData: Dict):
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
                 width='stretch',
                 column_config=config)
    formDetail(jobData)


def addCompanyAppliedJobsInfo(jobData):
    company = str(jobData['company']).lower().replace("'", "''")
    company = removeRegexChars(company)
    params = {'company': company,
              'id':  str(jobData['id'])}
    qry = SELECT_APPLIED_JOB_IDS_BY_COMPANY
    # For Joppy offers check also client
    # (client should be manually set by the user)
    if params['company'] == 'joppy' and jobData['client']:
        qry += SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT
        client = str(jobData['client']).lower()
        params |= {'client': client}
        company = removeRegexChars(jobData['client'])

    qry += SELECT_APPLIED_JOB_ORDER_BY
    rows = mysql.fetchAll(qry.format(**params))
    if len(rows) == 0:
        rows = searchPartialCompanyName(company, params, qry, rows)
    ids = ','.join([str(r[0]) for r in rows])
    if len(ids) > 0:
        dates = ' '.join(['  📅 '+formatDate(r[1].date()) for r in rows])
        jobData['company'] += ' <span style="font-size: small">' + \
            ':point_right: :warning: ' + \
            gotoPageByUrl(PAGE_VIEW_IDX, f'already applied {params["company"]}', ids) + \
            f' on {dates}</span>'


def formatDate(date):
    return date.strftime("%d-%m-%y")


def searchPartialCompanyName(company: str, params: dict, query: str, rows):
    companyWords = removeRegexChars(company).split(' ')
    while len(companyWords) > 1 and len(rows) == 0:
        companyWords = companyWords[:-1]
        words = ' '.join(companyWords)
        # FIXME: this doesn't work with MINSAIT (Indra Producción de Software
        part1 = re.escape(words)
        if len(part1) > 2 and part1 not in ['grupo']:
            params['company'] = f'(^| ){part1}($| )'
            showCodeSql(query, params)
            try:
                rows = mysql.fetchAll(query.format(**params))
            except Exception as e:
                st.error(e)
            params['company'] = words
    return rows


def removeRegexChars(txt: str):
    return re.sub(r'([()[\]|*+])', r'\\1', txt)
