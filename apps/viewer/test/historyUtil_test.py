from viewer.util.historyUtil import getHistoryKey, validValue, getFileName, sortedList


def test_valid_value():
    assert not validValue('id=123')
    assert not validValue('id =123')
    assert not validValue('id= 123')
    assert not validValue('id = 123')
    assert not validValue(' id = 123')
    assert not validValue('id = 123 ')
    assert not validValue(' id = 123 ')
    assert not validValue('id=48395 or id=48289 or id=56426 or id=47051 or id=30564 or id=31906 or id=48291 or id=45708 or id=56418')
    assert validValue("required_technologies rlike 'java([^script]|$)|python|scala|clojure' or title rlike 'java([^script]|$)|python|scala|clojure' or markdown rlike 'java([^script]|$)|python|scala|clojure'")


def test_get_history_key():
    assert getHistoryKey('a') == 'a_history'


def test_get_file_name_and_sorted_list():
    assert getFileName('keyName') == '.history/keyName.txt'
    values = {'b', 'A', 'c'}
    assert sortedList(values) == ['A', 'b', 'c']
