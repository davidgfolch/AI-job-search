import re
from pandas import DataFrame
import streamlit as st
from functools import reduce

from ai_job_search.tools.util import toBool


def initStates(keyValue: dict):
    if st.query_params.keys():
        for k in st.query_params.keys():
            if re.fullmatch(r'is([A-Z][a-z]+)+', k):
                setStateNoError(k, toBool(st.query_params[k]))
            else:
                setStateNoError(k, st.query_params[k])
    else:
        for k in keyValue.keys():
            if k not in st.session_state:
                setStateNoError(k, keyValue[k])


def printSessionState():
    with st.expander("StreamLite session state"):
        st.write(st.session_state)


def getState(key: str, default=None):
    value = st.session_state.get(key, default)
    if (isinstance(value, DataFrame) and len(value)) or value:
        if isinstance(value, str):
            if len(value.strip()) > 0:
                return value
        else:
            return value
    return default


def getStateBool(*keys: str, default=False) -> bool:
    return reduce(
        lambda x, y: x and y,
        (st.session_state.get(getBoolKeyName(key), default) for key in keys))


def getStateBoolValue(*keys: str):
    return reduce(lambda x, y: x and y,
                  (getStateBool(key) and getState(key) for key in keys))


def setState(key: str, value):
    st.session_state[key] = value


def setStateNoError(key: str, value):
    try:
        st.session_state[key] = value
    except Exception:
        pass


def getBoolKeyName(key: str):
    return f'is{key.title()}'
