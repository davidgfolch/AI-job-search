import streamlit as st

from commonlib.mysqlUtil import MysqlUtil

from viewer.statistics import appliedDiscardedByDateStats, createdByDate, createdByHours
from viewer.mysqlConn import mysqlCachedConnection
from viewer.util.stComponents import reloadButton


def showTotals():
    rows = MysqlUtil(mysqlCachedConnection()).fetchAll("""
select concat(count(id), ' Applied') as count from jobs where applied union all
select concat(count(id), ' Call or interview (rh)') as count from jobs
    where interview or interview_rh union all
select concat(count(id), ' Interview or tech/test') as count from jobs
    where interview_tech or interview_technical_test union all
select concat(count(id), ' Discarded') as count from jobs where discarded;""")
    totals = [row[0] for row in rows]
    st.markdown('#### Totals: ' + ', '.join(totals), unsafe_allow_html=True)


def stats():
    reloadButton()
    showTotals()
    createdByDate.run()
    createdByHours.run()
    appliedDiscardedByDateStats.run()


if __name__ == "__main__":
    stats()