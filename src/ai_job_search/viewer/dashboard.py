import streamlit as st
from ai_job_search.tools.mysqlUtil import MysqlUtil
from ai_job_search.viewer.statistics import (
    appliedDiscardedByDateStats, createdByDate,
    createdByHours)
from ai_job_search.viewer.streamlitConn import mysqlCachedConnection
from ai_job_search.viewer.util.stComponents import reloadButton


def showTotals():
    rows = MysqlUtil(mysqlCachedConnection()).fetchAll("""
select concat(count(id), ' Applied') as count from jobs where applied union all
select concat(count(id), ' Call or interview (rh)') as count from jobs
    where interview or interview_rh union all
select concat(count(id), ' Interview or tech/test') as count from jobs
    where interview_tech or interview_technical_test union all
select concat(count(id), ' Discarded') as count from jobs where discarded;""")
    totals = [row[0] for row in rows]
    st.markdown('#### Totals: ' + ', '.join(totals),
                unsafe_allow_html=True)


def stats():
    reloadButton()
    showTotals()
    createdByDate.run()
    createdByHours.run()
    appliedDiscardedByDateStats.run()
