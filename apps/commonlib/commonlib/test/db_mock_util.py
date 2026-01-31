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
