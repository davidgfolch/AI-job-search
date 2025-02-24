import json
import re
from pandas import DataFrame
import streamlit as st
from functools import reduce

from ai_job_search.tools.util import createFolder, listFiles, toBool


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


def saveSession(name: str):
    path = createFolder(getSessionFileName(name))
    with open(path, 'w') as f:
        session: dict = st.session_state.to_dict()
        ignoredKeysRegex = r'jobsListTable|.+Button|FormSubmitter.+'
        for k in list(session.keys()):
            if session[k] is None or \
                    isinstance(session[k], DataFrame) or \
                    re.match(ignoredKeysRegex, k, re.I) is not None:
                session.pop(k)
        st.write(session)
        f.write(json.dumps(session, default=lambda o: None))


def loadSession(name: str):
    path = createFolder(getSessionFileName(name))
    with open(path, 'r') as f:
        session: dict = json.loads(''.join(f.readlines()))
        st.session_state.clear()
        for k, v in session.items():
            st.session_state[k] = v


def getSessionFileName(name: str) -> str:
    if name.endswith('.json'):
        return f'.stSessionState/{name}'
    return f'.stSessionState/{name}.json'


def listSessionFiles(removeExtension=True) -> str:
    files = listFiles('.stSessionState')
    if removeExtension:
        return [f.replace('.json', '') for f in files]
    return files
