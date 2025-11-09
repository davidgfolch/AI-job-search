import streamlit as st
from commonlib.mysqlUtil import getConnection
import mysql.connector as mysqlConnector


@st.cache_resource()
def mysqlCachedConnection() -> mysqlConnector.MySQLConnection:
    return getConnection()