from viewer.util.historyUtil import getHistoryKey, validValue


def testValidValue():
    assert not validValue('id=123')
    assert not validValue('id =123')
    assert not validValue('id= 123')
    assert not validValue('id = 123')
    assert not validValue(' id = 123')
    assert not validValue('id = 123 ')
    assert not validValue(' id = 123 ')
    assert not validValue('id=48395 or id=48289 or id=56426 or id=47051 or id=30564 or id=31906 or id=48291 or id=45708 or id=56418')
    assert validValue("required_technologies rlike 'java([^script]|$)|python|scala|clojure' or title rlike 'java([^script]|$)|python|scala|clojure' or markdown rlike 'java([^script]|$)|python|scala|clojure'")


def testGetHistoryKey():
    assert getHistoryKey('a') == 'a_history'


def getFileName():
    assert getFileName('keyName') == '.history/keyName.txt'
