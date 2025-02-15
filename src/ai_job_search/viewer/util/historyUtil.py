import os
from pathlib import Path
import pandas
from pandas import DataFrame, Series
from ai_job_search.viewer.util.stStateUtil import getState, setState
import streamlit as st
from streamlit.delta_generator import DeltaGenerator


def historyButton(key: str, history: bool, container: DeltaGenerator = st):
    if history:
        help = addToHistory(key)
        help = '(Empty)' if not help else ', '.join(
            [f':blue[{h}]' if idx % 2 == 0 else f':green[{h}]'
             for idx, h in enumerate(help)])
        container.button(':clipboard:', help=help,
                         key=key+'_historyButton',
                         on_click=fieldHistory,
                         kwargs={'key': key})


@st.dialog("Field history", width='large')
def fieldHistory(key):
    data = pandas.DataFrame(getState(getHistoryKey(key)))
    data.insert(0, "Sel", False)
    res = st.data_editor(data=data,
                         #  column_config={'Sel': None, 'value': None},
                         width=600, use_container_width=True, hide_index=True,
                         key=key+'_history_table',
                         )
    historyOnChange(key, res)


def historyOnChange(key: str, df: DataFrame):
    if not df.empty:
        df = df[df.Sel]
        if not df.empty:
            selected = df.iloc[0]
            selected: Series = df["0"]
            selected = selected.values[0]
            setState(key, selected)
            st.rerun()


def addToHistory(key: str):
    historyKey = getHistoryKey(key)
    history: set = getState(historyKey, set())
    if not history or len(history) == 0:
        history = loadHistoryFromFile(key)
    value = getState(key)
    if value and value not in history:
        history.add(value.replace('\n', ''))
        saveHistoryToFile(key, history)
    setState(historyKey, history)
    return getState(historyKey)


def getHistoryKey(key):
    return key + '_history'


def loadHistoryFromFile(key) -> set:
    fName = getFileName(key)
    if os.path.isfile(fName):
        res = set(line.strip() for line in open(fName))
        return res
    return set()


def getFileName(key):
    return f'.history/{key}.txt'


def saveHistoryToFile(key, values: set) -> set:
    fName = Path(getFileName(key))
    fName.parent.mkdir(exist_ok=True, parents=True)
    with open(fName, 'w+') as output:
        output.writelines(v + '\n' for v in values)
