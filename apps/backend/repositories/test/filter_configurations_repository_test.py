import pytest
from unittest.mock import patch, MagicMock
from repositories.filter_configurations_repository import FilterConfigurationsRepository

@pytest.fixture
def mock_db():
    """Create a mock database that matches MysqlUtil interface"""
    mock = MagicMock()
    return mock

@pytest.fixture
def repo_with_mock(mock_db):
    """Create repository with mocked database"""
    repo = FilterConfigurationsRepository()
    with patch.object(repo, 'get_db', return_value=mock_db):
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        yield repo, mock_db

def test_find_all(repo_with_mock):
    """Test finding all configurations"""
    repo, mock_db = repo_with_mock
    
    # Mock the fetchAll to return rows
    mock_db.fetchAll.return_value = [
        (1, 'Config 1', '{"page": 1}', 1, 1, 0, '2024-01-01', None),
        (2, 'Config 2', '{"page": 2}', 0, 1, 1, '2024-01-02', None)
    ]
    
    result = repo.find_all()
    
    assert len(result) == 2
    assert result[0]['name'] == 'Config 1'
    assert result[0]['pinned'] == 0
    assert result[1]['pinned'] == 1
    assert result[0]['filters'] == {'page': 1}

def test_find_all_empty(repo_with_mock):
    """Test finding all when database is empty"""
    repo, mock_db = repo_with_mock
    mock_db.fetchAll.return_value = []
    
    result = repo.find_all()
    
    assert result == []

def test_find_by_id(repo_with_mock):
    """Test finding configuration by ID"""
    repo, mock_db = repo_with_mock
    
    mock_db.fetchOne.return_value = (1, 'Test', '{"page": 1}', 0, 1, 1, '2024-01-01', None)
    
    result = repo.find_by_id(1)
    
    assert result is not None
    assert result['id'] == 1
    assert result['name'] == 'Test'
    assert result['pinned'] == 1

def test_find_by_id_not_found(repo_with_mock):
    """Test finding non-existent configuration"""
    repo, mock_db = repo_with_mock
    mock_db.fetchOne.return_value = None
    
    result = repo.find_by_id(999)
    
    assert result is None

def test_find_by_name(repo_with_mock):
    """Test finding configuration by name"""
    repo, mock_db = repo_with_mock
    
    mock_db.fetchOne.return_value = (1, 'Test', '{"page": 1}', 0, 1, 0, '2024-01-01', None)
    
    result = repo.find_by_name('Test')
    
    assert result is not None
    assert result['name'] == 'Test'

def test_create(repo_with_mock):
    """Test creating new configuration"""
    repo, mock_db = repo_with_mock
    
    # We need to simulate _transaction executing the callback
    def side_effect(callback):
        # Create a mock cursor
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 123
        return callback(mock_cursor)
        
    mock_db._transaction.side_effect = side_effect
    
    result = repo.create('New Config', {'page': 1}, True, True, True)
    
    assert result == 123
    mock_db._transaction.assert_called_once()
    
    # Verify what happened inside the transaction
    # We need to check if execute was called on the cursor passed to callback
    # But since execute happened inside the side_effect, we can capture the cursor there?
    # Or rely on the fact that if it returns 123, the callback was executed.
    pass # If we reached here with 123, logic inside create's op function ran correctly (returned lastrowid)

def test_update(repo_with_mock):
    """Test updating configuration"""
    repo, mock_db = repo_with_mock
    
    result = repo.update(1, name='Updated', filters={'page': 2}, watched=True, pinned=True)
    
    assert result is True
    mock_db.executeAndCommit.assert_called_once()

def test_update_partial(repo_with_mock):
    """Test partial update (name only)"""
    repo, mock_db = repo_with_mock
    
    result = repo.update(1, name='Updated Only')
    
    assert result is True
    mock_db.executeAndCommit.assert_called_once()

def test_delete(repo_with_mock):
    """Test deleting configuration"""
    repo, mock_db = repo_with_mock
    
    result = repo.delete(1)
    
    assert result is True
    mock_db.executeAllAndCommit.assert_called_once()
    
    # Check that we delete config AND drop view
    queries = mock_db.executeAllAndCommit.call_args[0][0]
    assert len(queries) == 2
    
    # Order matters: Delete first, then Drop View (implicit commit) if we follow repository code
    # But wait, did I put delete first? Yes.
    assert "DELETE FROM filter_configurations" in queries[0]['query']
    assert queries[0]['params'] == [1]
    
    assert "DROP VIEW IF EXISTS config_view_1" in queries[1]['query']

def test_count(repo_with_mock):
    """Test counting configurations"""
    repo, mock_db = repo_with_mock
    mock_db.count.return_value = 5
    
    result = repo.count()
    
    assert result == 5
