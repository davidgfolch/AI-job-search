from pandas import DataFrame


def getIdsIndex(rows: DataFrame) -> int:
    try:
        return rows.columns.get_loc('Ids')
    except KeyError:
        return rows.columns.get_loc('Id')
