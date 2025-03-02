import streamlit as st
from ai_job_search.tools.mysqlUtil import getConnection
import mysql.connector as mysqlConnector


@st.cache_resource()
def mysqlCachedConnection() -> mysqlConnector.MySQLConnection:
    return getConnection()
