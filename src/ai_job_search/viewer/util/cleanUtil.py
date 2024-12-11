import re

from ai_job_search.viewer.util.stUtil import (
    KEY_SELECTED_IDS, PAGE_STATE_KEY, setState)


def gotoPage(page, selectedRows, idsIndex):
    setState(KEY_SELECTED_IDS, getAllIds(selectedRows, idsIndex))
    setState(PAGE_STATE_KEY, page)


def getAllIds(selectedRows, idsIndex, dropFirstByGroup=False, plainIdsStr=True):
    rows = list(selectedRows.iloc[row].iloc[idsIndex]
                for row in range(len(selectedRows)))
    if len(rows) == 0:
        return None
    if dropFirstByGroup:
        rows = list({re.sub(r'^[0-9]+,', '', row) for row in rows})
    if plainIdsStr:
        ids = ','.join([str(r) for r in rows])
        return ','.join(list(f"'{id}'" for id in ids.split(',')))
    return rows


def getFieldValue(row, colsArr, colName):
    return row[colsArr.index(colName)]


def removeNewestId(ids):
    idsArr = ids.split(',')
    idsArr.sort()
    idsArr.pop()
    return idsArr
