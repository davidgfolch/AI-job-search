import streamlit as st
from ai_job_search.viewer.cleaner import clean
from ai_job_search.viewer.util.stUtil import (
    PAGE_STATE_KEY, PAGES, getMessageInfo, printSessionState)
from ai_job_search.viewer.viewAndEdit import view

DEBUG = False

st.set_page_config(layout='wide', page_title="ai job search")
PAGES_MAP = {
    0: view,
    1: clean
}
c1, c2 = st.columns([10, 40])
selected = c1.segmented_control(
    label="Menu",
    options=PAGES.keys(),
    format_func=lambda i: PAGES[i],
    selection_mode="single",
    label_visibility='collapsed',
    default=0,
    key=PAGE_STATE_KEY
)
messageInfo = getMessageInfo()
if messageInfo:
    c2.info(messageInfo)
if selected is not None:
    selected = PAGES_MAP[selected]
    selected()
else:
    view()

if DEBUG:
    printSessionState()
