import os
import re
from pandas import DataFrame, Series
from ai_job_search.tools.util import createFolder
from ai_job_search.viewer.util.stStateUtil import (
    getBoolKeyName, getState, setState)
import streamlit as st
from streamlit.delta_generator import DeltaGenerator


def historyButton(key: str, history: bool, container: DeltaGenerator = st):
    if history and len(loadHistoryFromFile(key)) > 0:
        help = addToHistory(key)
        help = buttonTooltip(help)
        container.button(':clipboard:', help=help,
                         key=key+'_historyButton',
                         on_click=fieldHistory,
                         kwargs={'key': key})


def buttonTooltip(help):
    helpStr = '(Empty)' if not help else ', '.join(
        [f':blue[{h}]' if idx % 2 == 0 else f':green[{h}]'
         for idx, h in enumerate(help)])
    if len(helpStr) > 300:
        helpStr = f'{len(help)} items in field history'
    return helpStr


@st.dialog("Field history", width='large')
def fieldHistory(key):
    df = DataFrame(loadHistoryFromFile(key))
    df.insert(0, "Sel", False)
    st.write(f'File storage: :green[{getFileName(key)}]')
    colsConfig = {'Ids': None,
                  'Sel': st.column_config.Column(width='small'),
                  'Id': st.column_config.Column(width='small'),
                  'Title': st.column_config.Column(width='large'),
                  'Company': st.column_config.Column(width='large'),
                  'Created': st.column_config.Column(width='large'),
                  }
    res = st.data_editor(data=df,
                         column_config=colsConfig,
                         width=600, use_container_width=True, hide_index=True)
    historyOnChange(key, res)


def historyOnChange(key: str, df: DataFrame):
    if not df.empty:
        df = df[df.Sel]
        if not df.empty:
            selected = df.iloc[0]
            selected: Series = df["0"]
            selected = selected.values[0]
            setState(key, selected)
            setState(getBoolKeyName(key), True)
            st.rerun()


def addToHistory(key: str):
    value = getState(key)
    history = loadHistoryFromFile(key)
    if not validValue(value):
        return history
    if value and value not in history:
        history = set(history)
        history.add(value.replace('\n', ''))
        saveHistoryToFile(key, history)
    return history


def validValue(value: str):
    return value and len(re.findall('id *= *[0-9+]', value, re.I | re.M)) == 0


def getHistoryKey(key):
    return key + '_history'


def loadHistoryFromFile(key) -> list:
    fName = getFileName(key)
    if os.path.isfile(fName):
        with open(fName) as f:
            return sortedList(set(line.strip() for line in f.readlines()))
    return []


def getFileName(key):
    return f'.history/{key}.txt'


def saveHistoryToFile(key, values: set) -> set:
    path = createFolder(getFileName(key))
    with open(path, 'w+') as output:
        output.writelines(v + '\n' for v in sortedList(values))


def sortedList(values: set) -> list:
    return sorted(list(values), key=lambda x: x.lower())
