import re

from pandas import DataFrame

from ai_job_search.viewer.clean.cleanUtil import getIdsIndex


def getAllIds(selectedRows: DataFrame,
              dropFirstByGroup=False, plainIdsStr=True):
    rows = [selectedRows.iloc[row].iloc[getIdsIndex(selectedRows)]
            for row in range(len(selectedRows))]
    if len(rows) == 0:
        return None
    if dropFirstByGroup:
        rows = {re.sub(r'^[0-9]+,', '', row) for row in rows}
    if plainIdsStr:
        ids = ','.join([str(r) for r in rows])
        return ','.join(list(f"'{id}'" for id in ids.split(',')))
    return list(rows)


def getFieldValue(row, colsArr, colName):
    return row[colsArr.index(colName)]


def removeNewestId(ids):
    idsArr = ids.split(',')
    idsArr.sort()
    idsArr.pop()
    return idsArr
