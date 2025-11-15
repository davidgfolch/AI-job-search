import streamlit as st

from viewer.util import historyUtil
from viewer.viewAndEdit import view
from viewer.cleaner import clean
from viewer.dashboard import stats
from viewer.util.stStateUtil import printSessionState
from viewer.util.stUtil import getMessageInfo
from viewer.viewConstants import PAGE_STATE_KEY, PAGES

DEBUG = False

PAGES_MAP = {  # Also change PAGES
    0: view,
    1: clean,
    2: stats
}

def main():
    """Main application function"""
    historyUtil.init()
    
    st.set_page_config(layout='wide', page_title="ai job search")
    
    c1, c2 = st.columns([10, 40])

    selectedView = c1.segmented_control(
        label="Menu",
        options=PAGES.keys(),
        format_func=lambda i: PAGES[i],
        selection_mode="single",
        label_visibility='collapsed',
        key=PAGE_STATE_KEY
    )
    
    if messageInfo := getMessageInfo():
        c2.info(messageInfo)
    
    if selectedView is not None:
        selectedView = PAGES_MAP[selectedView]
        selectedView()
    else:
        view()
    
    if DEBUG:
        printSessionState()


if __name__ == "__main__" or "streamlit" in globals():
    main()
