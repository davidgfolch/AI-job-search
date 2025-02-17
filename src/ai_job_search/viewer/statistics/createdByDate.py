import pandas as pd
import streamlit as st
import plotly.express as px

from ai_job_search.tools.mysqlUtil import MysqlUtil

TITLE = "Job Postings by source & created date"


def run():
    with MysqlUtil() as mysql:
        query = """SELECT
            date(created) as dateCreated,
            count(*) as total,
            web_page as source
        from jobs
        group by dateCreated, web_page
        order by dateCreated"""
        df = pd.read_sql(query, mysql.conn)
        # Convert dateCreated to datetime for better plotting
        df['dateCreated'] = pd.to_datetime(df['dateCreated'])
        # Create a bar chart using Plotly Express
        fig = px.bar(df, x='dateCreated', y='total', color='source',
                     title=TITLE,
                     labels={'total': 'Number of Jobs',
                             'dateCreated': 'Date', 'source': 'Source'},
                     barmode='group')
        st.plotly_chart(fig)
