from unittest.mock import Mock, MagicMock

def create_mock_db(**kwargs):
    """
    Helper to create a mock database that supports context manager.
    
    Args:
        **kwargs: Configuration for the mock.
            - columns (list): list of column names for 'SHOW COLUMNS' query.
            - fetchAll (list): list of rows to return for fetchAll.
            - count (int): return value for count().
            - fetchOne (tuple|None): return value for fetchOne().
            - executeAndCommit (int): return value for executeAndCommit().
    
    Returns:
        Mock: A configured mock database object.
    """
    mock_db = Mock()
    columns = kwargs.get('columns', ['id', 'title', 'company'])
    data_rows = kwargs.get('fetchAll', [])
    
    def fetch_all_side_effect(query, params=None):
        if "SHOW COLUMNS" in str(query).upper():
            return [(c,) for c in columns]
        return data_rows

    mock_db.count.return_value = kwargs.get('count', 0)
    mock_db.fetchAll.side_effect = fetch_all_side_effect
    mock_db.fetchOne.return_value = kwargs.get('fetchOne', None)
    mock_db.getTableDdlColumnNames.return_value = columns
    mock_db.executeAndCommit.return_value = kwargs.get('executeAndCommit', 1)
    
    # Context manager support
    mock_db.__enter__ = Mock(return_value=mock_db)
    mock_db.__exit__ = Mock(return_value=False)
    
    return mock_db

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
