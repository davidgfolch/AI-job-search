import pandas as pd
import streamlit as st
import plotly.express as px

from ai_job_search.tools.mysqlUtil import MysqlUtil


def run():
    with MysqlUtil() as mysql:
        query = """SELECT
            HOUR(created) AS hour,
            max(web_page) as source,
            COUNT(*) AS total
        FROM jobs
        GROUP BY HOUR(created), web_page
        order by web_page, hour"""
        df = pd.read_sql(query, mysql.conn)
        fig = px.bar(df, x='hour', y='total', color='source',
                     title="Job Postings by Source & day time",
                     labels={'total': 'Number of Jobs',
                             'hour': 'Hour', 'source': 'Source'},
                     barmode='group')
        st.plotly_chart(fig)
