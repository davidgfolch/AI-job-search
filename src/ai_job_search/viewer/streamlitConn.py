import streamlit as st
from ai_job_search.tools.mysqlUtil import MysqlUtil


@st.cache_resource()
def mysql():
    return MysqlUtil()
