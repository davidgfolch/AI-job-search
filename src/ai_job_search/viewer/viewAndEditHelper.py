import streamlit as st
# from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from streamlit.column_config import CheckboxColumn
from pandas import DataFrame
from ai_job_search.tools.mysqlUtil import (
    QRY_SELECT_JOBS_VIEWER, binaryColumnIgnoreCase, getColumnTranslated)
from ai_job_search.tools.sqlUtil import getAndFilter
from ai_job_search.viewer.util.stComponents import (
    checkAndInput, checkAndPills, sessionStateButtons)
from ai_job_search.viewer.util.stStateUtil import (
    getBoolKeyName, getStateBool, getStateBoolValue, setState)
from ai_job_search.viewer.util.stUtil import (
    getState, inColumns, scapeLatex)
from ai_job_search.viewer.util.viewUtil import (
    KEY_SELECTED_IDS, fmtDetailOpField, formatDateTime)
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
def table(df: DataFrame, columnsOrder, visibleColumns) -> DataFrame:
    dfWithSelections = df.copy()
    preSelectedRows = getState(FF_KEY_PRESELECTED_ROWS, [])
    if len(preSelectedRows) == 1:
        setState(FF_KEY_SINGLE_SELECT, 1)
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
        column_config=getTableColsConfig(columnsOrder, visibleColumns),
        use_container_width=True,
        height=getState(FF_KEY_LIST_HEIGHT, HEIGHT),
        key='jobsListTable',
    )
    selectedRows = df[editedDf.Sel]
    setState('selectedRows', selectedRows)
    return selectedRows


def selectNext(max: int):
    rows: set = getState(FF_KEY_PRESELECTED_ROWS, None)
    if rows is not None and len(rows) == 1 and int(rows[0]) < max:
        nextRow = str(int(rows[0])+1)
        setQueryParamOrState(FF_KEY_PRESELECTED_ROWS, nextRow, [nextRow])


def selectPrevious():
    rows: set = getState(FF_KEY_PRESELECTED_ROWS, None)
    if rows is not None and len(rows) == 1 and int(rows[0]) > 0:
        prevRow = str(int(rows[0])-1)
    setQueryParamOrState(FF_KEY_PRESELECTED_ROWS, prevRow, [prevRow])


def setQueryParamOrState(param: str, paramValue, stateValue=None):
    """Sets query_params if it exists in url (overrides it), otherwise sets the state."""
    if st.query_params.get(param):
        st.query_params[param] = paramValue
    else:
        setState(param, stateValue if stateValue else paramValue)


# TODO: NEW TABLE
# def tableV2(df: DataFrame, columnsOrder: List[str],
#             visibleColumns: List[str]) -> DataFrame:
#     # 1. Filtrar columnas existentes
#     cols = df.columns.tolist()
#     columnsOrder = [col for col in columnsOrder if col in cols]
#     visibleColumns = [col for col in visibleColumns if col in cols]
#     # 2. Reordenar y filtrar columnas
#     df = df[columnsOrder]  # Reordenar según fieldsSorted
#     df = df[visibleColumns]  # Filtrar columnas visibles
#     # 3. Configurar la grilla
#     gb = GridOptionsBuilder.from_dataframe(df)
#     # 4. Configurar columnas (ancho, etiquetas, etc.)
#     for col in df.columns:
#         gb.configure_column(col,
#                             header_name=getColumnTranslated(col),
#                             width=200)  # Ajusta el ancho según necesidades
#     # 5. Selección de filas con un click
#     gb.configure_selection(
#         selection_mode="multiple",  # 'single' para selección única
#         use_checkbox=False,  # True para mostrar checkboxes
#         pre_selected_rows=getState(FF_KEY_PRESELECTED_ROWS, []))
#     grid_options = gb.build()
#     # 6. Renderizar la tabla
#     grid_response = AgGrid(df,
#                            gridOptions=grid_options,
#                            height=getState(FF_KEY_LIST_HEIGHT, HEIGHT),
#                            update_mode=GridUpdateMode.SELECTION_CHANGED,
#                            key='jobsListTable',
#                            allow_unsafe_jmespath=True)
#     # 7. Obtener filas seleccionadas
#     selected_rows = grid_response["selected_rows"]
#     # selected_df = DataFrame(selected_rows).drop(
#     #     columns=['_selectedRowNodeInfo'])
#     selected_df = DataFrame(selected_rows)
#     # 8. Actualizar estado
#     setState('selectedRows', selected_df)
#     return selected_df


def getTableColsConfig(fields: list[str], visibleColumns, selector=True):
    # https://docs.streamlit.io/develop/api-reference/data/st.column_config
    cfg = {}
    if selector:
        cfg["Sel"] = CheckboxColumn(required=True, width=25)
    cfg["0"] = None  # remove id from view, or set to 'id'
    # SORT VISIBLE COLUMNS FIRST
    for idx, c in enumerate(fields):
        if idx > 0 and c in visibleColumns:
            cTranslated = getColumnTranslated(c)
            width = 'medium'
            if cTranslated == 'Sel':
                width = 'small'
            elif cTranslated == 'Title':
                width = 'large'
            cfg[idx+2] = st.column_config.Column(
                label=cTranslated,
                width=width)
        else:
            cfg[idx+2] = None
    return cfg


def detailForSingleSelection():
    st.divider()
    c1, c2, _ = st.columns([4, 3, 30])
    c1.button('Ignore', help='Mark as ignored and Save',
              key='ignore2Button', kwargs={'boolField': 'ignored'},
              on_click=markAs)
    c2.button('Seen', help='Mark as Seen and Save',
              key='seen2Button', kwargs={'boolField': 'seen'},
              on_click=markAs)


def formFilter():
    if getStateBool(FF_KEY_BOOL_FIELDS, FF_KEY_BOOL_NOT_FIELDS):
        if res := removeFiltersInNotFilters():
            setState(FF_KEY_BOOL_NOT_FIELDS, res)
    formFilterByIdsSetup()
    sessionStateButtons()
    with st.expander('Search filters'):
        inColumns([
            (6, lambda _: checkAndInput(SEARCH_INPUT_HELP, FF_KEY_SEARCH,
                                        withContainer=False,
                                        withHistory=True)),
            (1, lambda _: checkAndInput('Days old', FF_KEY_DAYS_OLD,
                                        withContainer=False)),
            (3, lambda _: checkAndInput("Salary regular expression",
                                        FF_KEY_SALARY,
                                        withContainer=False,
                                        withHistory=True)),
            (3, lambda _: checkAndInput('Sort by columns', FF_KEY_ORDER,
                                        withContainer=False,
                                        withHistory=True))])
        inColumns([
            (1, lambda _: checkAndPills(
                'Status filter', FIELDS_BOOL, FF_KEY_BOOL_FIELDS)),
            (1, lambda _: checkAndPills('Status NOT filter',
             FIELDS_BOOL, FF_KEY_BOOL_NOT_FIELDS))
        ])
        checkAndInput("SQL where filters", FF_KEY_WHERE,
                      withContainer=False,
                      withHistory=True)


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


def tableFooter(totalResults, filterResCnt, totalSelected,
                selectedRows: DataFrame):
    totals = f'<p style="text-align:right">{totalSelected} ' + \
        f'selected ({filterResCnt} filtered, ' + \
        f'{totalResults} total)</p>'
    st.write(totals, unsafe_allow_html=True)
    if filterResCnt < 1:
        return
    singleSel = getState(FF_KEY_SINGLE_SELECT) == 1
    idxValues = selectedRows.index.values
    selected = idxValues[0] if len(idxValues) > 0 else None
    enabledPrevNext = singleSel and selected is not None
    prevEnabled = enabledPrevNext and selected > 0
    nextEnabled = enabledPrevNext and selected < filterResCnt-1
    columns = \
        [(3, lambda _: st.button('Ignore',
                                 help='Mark as ignored and Save',
                                 kwargs={'boolField': 'ignored'},
                                 disabled=totalSelected < 1,
                                 on_click=markAs)),
            (3, lambda _: st.button('Seen',
                                    help='Mark as Seen and Save',
                                    kwargs={'boolField': 'seen'},
                                    disabled=totalSelected < 1,
                                    on_click=markAs)),
            (3, lambda _: st.button('Delete', 'deleteButton',
                                    help='Delete selected job(s)',
                                    disabled=totalSelected < 1,
                                    on_click=deleteSelectedRows,
                                    type="primary")),
            (1, lambda _: st.button('<', 'prevButton',
                                    help='Select & see previous job',
                                    disabled=not prevEnabled,
                                    on_click=selectPrevious,
                                    type="primary")),
            (1, lambda _: st.button('&gt;', 'nextButton',  # >
                                    help='Select & see next job',
                                    disabled=not nextEnabled,
                                    on_click=selectNext,
                                    kwargs={'max': filterResCnt-1},
                                    type="primary")),
            (1, lambda _: st.write('|')),
            (5, lambda _: st.toggle('Single select',
                                    key=FF_KEY_SINGLE_SELECT)),
            (5, lambda _: st.number_input('Height', key=FF_KEY_LIST_HEIGHT,
                                          value=HEIGHT, step=100,
                                          label_visibility='collapsed')),
            (5, lambda _: st.number_input('Columns width',
                                          key=FF_KEY_COLUMNS_WIDTH,
                                          value=COLUMNS_WIDTH, step=0.1,
                                          label_visibility='collapsed'))

         ]
    inColumns(kwargs={'vertical_alignment': 'center'},
              columns=columns)


def showDetail(jobData: dict):
    data = scapeLatex(jobData, ['markdown', 'title'])
    formatDateTime(jobData)
    data = {k: (data[k] if data[k] else None) for k in data.keys()}
    str = DETAIL_FORMAT.format(**data)
    str += fmtDetailOpField(data, 'client')
    reqSkills = fmtDetailOpField(data, 'required_technologies', 'Required', 2)
    opSkills = fmtDetailOpField(data, 'optional_technologies', 'Optional', 2)
    if reqSkills + opSkills != '':
        str += ''.join(["- Skills\n", reqSkills, opSkills])
    if error := jobData.get('ai_enrich_error', None):
        str += f'- :red[AI enrich error:] {error}'
    st.markdown(str, unsafe_allow_html=True)
    salary = fmtDetailOpField(data, 'salary')
    if salary != '':
        c1, c2 = st.columns(2)
        c1.write(salary)
        c2.button('', icon='🗑️', key='trashButton',
                  on_click=deleteSalary, kwargs={'id': jobData['id']})
    if val := data.get('comments'):
        with st.expander('Comments', expanded=True):
            st.markdown(val)
    st.markdown(data['markdown'])
