import streamlit as st
from ai_job_search.viewer.clean import clean
from ai_job_search.viewer.stUtil import PAGE_CLEAN, PAGE_STATE_KEY, PAGE_VIEW
from ai_job_search.viewer.viewAndEdit import view


st.set_page_config(layout='wide', page_title="ai job search")

PAGES_ROUTER = {
    PAGE_VIEW: view,
    PAGE_CLEAN: clean
}

selectedPageFnc = st.sidebar.selectbox("AI job search pages",
                                       PAGES_ROUTER.keys(),
                                       key=PAGE_STATE_KEY)
PAGES_ROUTER[selectedPageFnc]()
