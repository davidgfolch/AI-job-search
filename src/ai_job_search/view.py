import streamlit as st
from ai_job_search.viewer.cleaner import clean
from ai_job_search.viewer.util.stUtil import (
    PAGE_STATE_KEY, PAGES, initStates)
from ai_job_search.viewer.viewAndEdit import view


st.set_page_config(layout='wide', page_title="ai job search")
# initStates({
#     PAGE_STATE_KEY: PAGE_VIEW
# })

# PAGES_ROUTER = {
#     PAGE_VIEW: view,
#     PAGE_CLEAN: clean
# }

# selected = st.sidebar.selectbox("AI job search pages",
#                                        PAGES_ROUTER.keys(),
#                                        key=PAGE_STATE_KEY)
# PAGES_ROUTER[selected]()


initStates({
    PAGE_STATE_KEY: 0
})
PAGES_MAP = {
    0: view,
    1: clean
}
selected = st.segmented_control(
    label="Menu",
    options=PAGES.keys(),
    format_func=lambda i: PAGES[i],
    selection_mode="single",
    label_visibility='collapsed',
    default=0,
    key=PAGE_STATE_KEY
)
if selected is not None:
    selected = PAGES_MAP[selected]
    selected()
else:
    view()
