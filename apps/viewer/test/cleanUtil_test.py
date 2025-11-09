import pytest
from pandas import DataFrame
from viewer.clean.cleanUtil import getAllIds, getFieldValue, getIdsIndex

class TestGetAllIds:
    def test_get_all_ids(self):
        df = DataFrame({'Id': [1, 2, 3], 'Title': ['A', 'B', 'C']})
        assert getAllIds(df) == "'1','2','3'"
        
        df = DataFrame({'Id': []})
        assert getAllIds(df) is None
        
        df = DataFrame({'Ids': ['1,2', '3,4'], 'Title': ['A', 'B']})
        assert getAllIds(df) == "'1','2','3','4'"
        
        df = DataFrame({'Ids': ['1,2,3', '4,5,6'], 'Title': ['A', 'B']})
        result = getAllIds(df, dropFirstByGroup=True)
        assert set(result.split(',')) == {"'2'", "'3'", "'5'", "'6'"}
        
        df = DataFrame({'Id': [1, 2, 3], 'Title': ['A', 'B', 'C']})
        assert getAllIds(df, plainIdsStr=False) == [1, 2, 3]
        
        df = DataFrame({'Ids': ['1,2,3', '4,5,6'], 'Title': ['A', 'B']})
        result = getAllIds(df, dropFirstByGroup=True, plainIdsStr=False)
        assert set(result) == {'2,3', '5,6'}

class TestGetFieldValue:
    def test_get_field_value(self):
        row = ['John', 25, 'Engineer']
        cols = ['name', 'age', 'job']
        assert getFieldValue(row, cols, 'age') == 25
        assert getFieldValue(row, cols, 'name') == 'John'
        
        with pytest.raises(ValueError):
            getFieldValue(row, cols, 'salary')

class TestGetIdsIndex:
    def test_get_ids_index(self):
        df = DataFrame({'Title': ['A'], 'Ids': [1], 'Company': ['B']})
        assert getIdsIndex(df) == 1
        
        df = DataFrame({'Title': ['A'], 'Id': [1], 'Company': ['B']})
        assert getIdsIndex(df) == 1
        
        df = DataFrame({'Ids': [1], 'Title': ['A'], 'Company': ['B']})
        assert getIdsIndex(df) == 0
        
        with pytest.raises(KeyError):
            df = DataFrame({'Title': ['A'], 'Company': ['B']})
            getIdsIndex(df)