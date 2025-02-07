import re


def getAllIds(selectedRows, idsIndex,
              dropFirstByGroup=False, plainIdsStr=True):
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
