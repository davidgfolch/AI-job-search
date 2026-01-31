from commonlib.test.db_mock_util import create_mock_db
from unittest.mock import MagicMock

def test_create_mock_db_structure():
    mock_db = create_mock_db()
    
    # Check context manager
    with mock_db as db:
        assert db == mock_db
        
    # Check default methods exist
    assert hasattr(mock_db, 'fetchAll')
    assert hasattr(mock_db, 'fetchOne')
    assert hasattr(mock_db, 'executeAndCommit')
    
def test_create_mock_db_custom_values():
    mock_db = create_mock_db(
        count=10, 
        executeAndCommit=5, 
        fetchOne=("row",),
        fetchAll=[("r1",), ("r2",)]
    )
    
    assert mock_db.count() == 10
    assert mock_db.executeAndCommit("UPDATE") == 5
    assert mock_db.fetchOne("SELECT") == ("row",)
    assert mock_db.fetchAll("SELECT") == [("r1",), ("r2",)]
    
def test_show_columns_behavior():
    cols = ['a', 'b']
    mock_db = create_mock_db(columns=cols)
    
    result = mock_db.fetchAll("SHOW COLUMNS FROM t")
    # Should return list of tuples
    assert result == [('a',), ('b',)]
