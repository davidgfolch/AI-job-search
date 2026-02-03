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
        (1, 'Config 1', '{"page": 1}', 1, 1, '2024-01-01', None),
        (2, 'Config 2', '{"page": 2}', 0, 1, '2024-01-02', None)
    ]
    
    result = repo.find_all()
    
    assert len(result) == 2
    assert result[0]['name'] == 'Config 1'
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
    
    mock_db.fetchOne.return_value = (1, 'Test', '{"page": 1}', 0, 1, '2024-01-01', None)
    
    result = repo.find_by_id(1)
    
    assert result is not None
    assert result['id'] == 1
    assert result['name'] == 'Test'

def test_find_by_id_not_found(repo_with_mock):
    """Test finding non-existent configuration"""
    repo, mock_db = repo_with_mock
    mock_db.fetchOne.return_value = None
    
    result = repo.find_by_id(999)
    
    assert result is None

def test_find_by_name(repo_with_mock):
    """Test finding configuration by name"""
    repo, mock_db = repo_with_mock
    
    mock_db.fetchOne.return_value = (1, 'Test', '{"page": 1}', 0, 1, '2024-01-01', None)
    
    result = repo.find_by_name('Test')
    
    assert result is not None
    assert result['name'] == 'Test'

def test_create(repo_with_mock):
    """Test creating new configuration"""
    repo, mock_db = repo_with_mock
    
    # Mock the last insert ID
    mock_db.fetchOne.return_value = (123,)
    
    result = repo.create('New Config', {'page': 1}, True)
    
    assert result == 123
    mock_db.executeAndCommit.assert_called_once()

def test_update(repo_with_mock):
    """Test updating configuration"""
    repo, mock_db = repo_with_mock
    
    result = repo.update(1, name='Updated', filters={'page': 2}, notify=True)
    
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
    mock_db.executeAndCommit.assert_called_once()

def test_count(repo_with_mock):
    """Test counting configurations"""
    repo, mock_db = repo_with_mock
    mock_db.count.return_value = 5
    
    result = repo.count()
    
    assert result == 5
