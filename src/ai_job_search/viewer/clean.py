import re
import streamlit as st
import pandas as pd
from viewer.stUtil import (KEY_SELECTED_IDS, PAGE_STATE_KEY, PAGE_VIEW,
                           getStateOrDefault, setState, stripFields)
from tools.mysqlUtil import (MysqlUtil)

QUERY_DESCRIPTION = """Show all repeated job offers by `title,company`,
where `user didn't change states`:
\nseen,like,ignored,applied,discarded,closed,interview_rh,interview,
interview_tech,interview_technical_test,interview_technical_test_done"""
COLUMNS = stripFields('Counter,Ids,Title,Company')
IDS_IDX = 1
SELECT_DUPLICATEDS = """
select r.counter, r.ids, r.title, r.company
from (select count(*) as counter,
            GROUP_CONCAT(CAST(id as CHAR(50)) SEPARATOR ',') as ids,
            max(created) as max_created,  -- to delete all, but last
            title, company
        from jobs
        where not (seen or `like` or ignored or applied or discarded or
                    closed or interview_rh or interview or interview_tech or
                    interview_technical_test or interview_technical_test_done)
        group by title, company
    ) as r
where r.counter>1
order by r.counter desc, r.title, r.company, r.max_created desc"""
# where DATE(created) < DATE_SUB(CURDATE(), INTERVAL 7 DAY)
DELETE_BY_IDS = 'delete from jobs where id in ({ids})'


def gotoPage(page, selectedRows):
    setState(KEY_SELECTED_IDS, getAllIds(selectedRows))
    setState(PAGE_STATE_KEY, page)


def getAllIds(selectedRows, dropFirstByGroup=False):
    rows = list(selectedRows.iloc[row][IDS_IDX]
                for row in range(len(selectedRows)))
    if len(rows) == 0:
        return None
    if dropFirstByGroup:
        rows = list({re.sub(r'^[0-9]+,', '', row) for row in rows})
    ids = ','.join(rows)
    return ','.join(list(f"'{id}'" for id in ids.split(',')))


def delete(selectedRows):
    # TODO: merge old jobs user info into the last one
    ids = getAllIds(selectedRows, dropFirstByGroup=True)
    query = DELETE_BY_IDS.format(**{'ids': ids})
    st.code(query)
    mysql = MysqlUtil()
    try:
        res = mysql.executeAndCommit(query)
    finally:
        mysql.close()
    st.info(f'{res} duplicated jobs deleted')


def clean():
    mysql = MysqlUtil()
    try:
        query = SELECT_DUPLICATEDS.strip()
        with st.expander(QUERY_DESCRIPTION):
            if st.toggle('Edit query'):
                query = st.text_area('Query', query, key='cleanSelectQuery',
                                     height=300)
            st.code(query if query else SELECT_DUPLICATEDS.strip(), 'sql')
        df = pd.DataFrame(mysql.fetchAll(query), columns=COLUMNS)
        if len(df) > 0:
            dfWithSelections = df.copy()
            dfWithSelections.insert(
                0, "Sel", getStateOrDefault('selectAll', False))
            rows = st.data_editor(dfWithSelections, use_container_width=True,
                                  hide_index=True,
                                  column_config={'Ids': None}, height=400)
            selectedRows = df[rows.Sel]
            totalSelectedRows = len(selectedRows)
            ids = getAllIds(selectedRows)
            totalSelectedIds = len(ids.split(',')) if ids else 0
            st.write(f'{totalSelectedIds} selected jobs ',
                     f'({totalSelectedRows} selected rows)')
            c1, c2 = st.columns([3, 20])
            disabled = totalSelectedIds < 1
            c1.button('Select all', key='selectAll', type='primary')
            c1.button('Delete (old duplicateds) in selection', on_click=delete,
                      kwargs={'selectedRows': selectedRows},
                      type='primary', disabled=disabled)
            c1.button('View', on_click=gotoPage,
                      kwargs={'page': PAGE_VIEW,
                              'selectedRows': selectedRows},
                      type='primary', disabled=disabled)
            if not disabled:
                c2.dataframe(selectedRows, hide_index=True,
                             use_container_width=True)
        else:
            st.warning('No results found for query.')
    finally:
        mysql.close()
