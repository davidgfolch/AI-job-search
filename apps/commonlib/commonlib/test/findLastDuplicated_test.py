import pytest
from unittest.mock import MagicMock
from commonlib.findLastDuplicated import find_last_duplicated

def test_find_last_duplicated_found():
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.return_value = [(123,)]
    
    result = find_last_duplicated(mock_mysql, "Software Engineer", "Tech Corp")
    
    assert result == 123
    mock_mysql.fetchAll.assert_called_once()
    args = mock_mysql.fetchAll.call_args[0]
    assert args[1] == ["Software Engineer", "Tech Corp"]

def test_find_last_duplicated_not_found():
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.return_value = []
    
    result = find_last_duplicated(mock_mysql, "Software Engineer", "Tech Corp")
    
    assert result is None

def test_find_last_duplicated_joppy():
    mock_mysql = MagicMock()
    
    result = find_last_duplicated(mock_mysql, "Software Engineer", "Joppy")
    
    assert result is None
    mock_mysql.fetchAll.assert_not_called()

def test_find_last_duplicated_empty_args():
    mock_mysql = MagicMock()
    
    assert find_last_duplicated(mock_mysql, "", "Tech Corp") is None
    assert find_last_duplicated(mock_mysql, "Title", "") is None
    mock_mysql.fetchAll.assert_not_called()
