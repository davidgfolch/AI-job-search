import pytest
from unittest.mock import MagicMock, patch
from commonlib.mergeDuplicates import (
    stripFields,
    getSelect,
    _mergeJobDuplicates,
    getFieldValue,
    _mergeAll,
    mergeDuplicatedJobs,
    COLS_ARR,
    COL_COMPANY_IDX
)

def test_stripFields():
    input_str = "  field1 , field2\n, field3  "
    expected = ["field1", "field2", "field3"]
    assert stripFields(input_str) == expected

def test_getSelect():
    query = getSelect()
    assert "select r.counter, r.ids, r.title, r.company" in query
    assert "from jobs" in query
    assert "group by title, company" in query
    assert "having r.counter>1" not in query # It's in the outer query where clause
    assert "where r.counter>1" in query

def test_getFieldValue():
    row = ["val1", "val2", "val3"]
    cols = ["col1", "col2", "col3"]
    assert getFieldValue(row, cols, "col2") == "val2"

def test_mergeJobDuplicates():
    # Setup
    # COLS_ARR usually has 'id', 'title', ... 'company' ...
    # Let's mock COLS_ARR for this test to be sure of indices, 
    # but the function uses the global COLS_ARR. 
    # We should rely on the actual COLS_ARR structure or mock it if possible.
    # For now, let's construct a row that matches the real COLS_ARR length and content types.
    
    # We need to know the index of 'title' and 'company' and 'id' in COLS_ARR
    id_idx = COLS_ARR.index('id')
    title_idx = COLS_ARR.index('title')
    company_idx = COLS_ARR.index('company')
    
    # Create a dummy row with None for most fields, but values for required ones
    row1 = [None] * len(COLS_ARR)
    row1[id_idx] = 1
    row1[title_idx] = "Software Engineer"
    row1[company_idx] = "Tech Corp"
    
    # Add some data to merge
    # Assuming there are other fields after company that are not 'created'
    # Let's find a field to test merging.
    # DB_FIELDS_MERGE includes 'salary'.
    if 'salary' in COLS_ARR:
        salary_idx = COLS_ARR.index('salary')
        row1[salary_idx] = "100k"

    rows = [row1]
    ids = "1,2"
    
    id_res, merged, out = _mergeJobDuplicates(rows, ids)
    
    assert id_res == 1
    assert merged.get('salary') == "100k"
    assert "Software Engineer" in out[0]
    assert "Tech Corp" in out[0]

def test_mergeAll():
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.return_value = [] # Mock empty result for the inner query first
    
    # We need to mock _mergeJobDuplicates to return something valid or ensure fetchAll returns valid rows
    # Let's mock the inner logic by providing return values for fetchAll
    
    # Construct a row that mimics what fetchAll returns for SELECT_FOR_MERGE
    # It needs to match COLS_ARR
    row = [None] * len(COLS_ARR)
    row[COLS_ARR.index('id')] = 10
    row[COLS_ARR.index('title')] = "Dev"
    row[COLS_ARR.index('company')] = "Comp"
    
    mock_mysql.fetchAll.return_value = [row]
    mock_mysql.executeAllAndCommit.return_value = 1
    
    rowsIds = ["10,11"]
    
    results = _mergeAll(mock_mysql, rowsIds)
    
    assert len(results) == 1
    assert len(results[0]) == 4 # arr/query + update + delete + text
    
    # Verify executeAllAndCommit was called
    mock_mysql.executeAllAndCommit.assert_called_once()
    args = mock_mysql.executeAllAndCommit.call_args[0][0]
    assert len(args) == 2 # Update and Delete queries

@patch('commonlib.mergeDuplicates._mergeAll')
def test_mergeDuplicatedJobs(mock_mergeAll):
    mock_mysql = MagicMock()
    # Mock rows for the initial select
    # select r.counter, r.ids, r.title, r.company
    mock_mysql.fetchAll.return_value = [
        (2, "1,2", "Title", "Company")
    ]
    
    mock_mergeAll.return_value = [[{'text': 'Done'}]]
    
    mergeDuplicatedJobs(mock_mysql, "SELECT ...")
    
    mock_mergeAll.assert_called_once()
    call_args = mock_mergeAll.call_args
    assert call_args[0][1] == ["1,2"]

@patch('commonlib.mergeDuplicates._mergeAll')
def test_mergeDuplicatedJobs_no_rows(mock_mergeAll):
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.return_value = []
    
    mergeDuplicatedJobs(mock_mysql, "SELECT ...")
    
    mock_mergeAll.assert_not_called()
