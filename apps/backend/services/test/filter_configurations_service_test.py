import pytest
from unittest.mock import patch, MagicMock
from services.filter_configurations_service import FilterConfigurationsService

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def service(mock_repo):
    return FilterConfigurationsService(repo=mock_repo)

def test_get_all_seeds_when_empty(service, mock_repo):
    """Test auto-seeding when database is empty"""
    mock_repo.count.return_value = 0
    mock_repo.find_all.return_value = [
        {'id': 1, 'name': 'Config 1', 'filters': {}, 'watched': False, 'created': '2024-01-01', 'modified': None}
    ]
    
    with patch.object(service, 'seed_defaults') as mock_seed:
        result = service.get_all()
        mock_seed.assert_called_once()
        assert len(result) == 1

def test_get_all_skips_seeding_when_not_empty(service, mock_repo):
    """Test no seeding when database already has data"""
    mock_repo.count.return_value = 5
    mock_repo.find_all.return_value = [
        {'id': 1, 'name': 'Config 1', 'filters': {}, 'watched': False, 'created': '2024-01-01', 'modified': None}
    ]
    
    with patch.object(service, 'seed_defaults') as mock_seed:
        result = service.get_all()
        mock_seed.assert_not_called()

def test_get_by_id_found(service, mock_repo):
    """Test getting configuration by ID"""
    mock_repo.find_by_id.return_value = {
        'id': 1, 'name': 'Test', 'filters': {}, 'watched': False, 'statistics': True, 'pinned': False, 'created': '2024-01-01', 'modified': None
    }
    
    result = service.get_by_id(1)
    assert result['id'] == 1

def test_get_by_id_not_found(service, mock_repo):
    """Test error when configuration not found"""
    mock_repo.find_by_id.return_value = None
    
    with pytest.raises(ValueError, match="not found"):
        service.get_by_id(999)

def test_create_success(service, mock_repo):
    """Test creating new configuration"""
    mock_repo.find_by_name.return_value = None
    mock_repo.create.return_value = 1
    mock_repo.find_by_id.return_value = {
        'id': 1, 'name': 'New Config', 'filters': {}, 'watched': False, 'statistics': True, 'pinned': True, 'ordering': 0, 'created': '2024-01-01', 'modified': None
    }
    
    result = service.create('New Config', {}, False, True, True)
    assert result['id'] == 1
    assert result['pinned'] is True
    mock_repo.create.assert_called_once_with('New Config', {}, False, True, True, 0)

def test_create_duplicate_name(service, mock_repo):
    """Test error when creating config with duplicate name"""
    mock_repo.find_by_name.return_value = {'id': 1, 'name': 'Existing'}
    
    with pytest.raises(ValueError, match="already exists"):
        service.create('Existing', {}, False)

def test_update_success(service, mock_repo):
    """Test updating existing configuration"""
    mock_repo.find_by_id.side_effect = [
        {'id': 1, 'name': 'Old', 'filters': {}, 'watched': False, 'statistics': True, 'pinned': False, 'created': '2024-01-01', 'modified': None},
        {'id': 1, 'name': 'New', 'filters': {}, 'watched': True, 'statistics': True, 'pinned': True, 'created': '2024-01-01', 'modified': None}
    ]
    mock_repo.find_by_name.return_value = None
    mock_repo.update.return_value = True
    
    result = service.update(1, name='New', pinned=True)
    assert result['name'] == 'New'
    assert result['pinned'] is True

def test_update_duplicate_name(service, mock_repo):
    """Test error when updating to duplicate name"""
    mock_repo.find_by_id.return_value = {'id': 1, 'name': 'Current', 'filters': {}, 'watched': False}
    mock_repo.find_by_name.return_value = {'id': 2, 'name': 'Existing'}
    
    with pytest.raises(ValueError, match="already exists"):
        service.update(1, name='Existing')

def test_delete_success(service, mock_repo):
    """Test deleting configuration"""
    mock_repo.find_by_id.return_value = {'id': 1, 'name': 'Test'}
    mock_repo.delete.return_value = True
    
    result = service.delete(1)
    assert result is True
    mock_repo.delete.assert_called_once_with(1)

def test_delete_not_found(service, mock_repo):
    """Test error when deleting non-existent configuration"""
    mock_repo.find_by_id.return_value = None
    
    with pytest.raises(ValueError, match="not found"):
        service.delete(999)

@patch('services.filter_configurations_service.os.path.exists')
@patch('services.filter_configurations_service.open')
@patch('services.filter_configurations_service.json.load')
def test_seed_defaults(mock_json_load, mock_open, mock_exists, service, mock_repo):
    """Test seeding default configurations from JSON file"""
    mock_exists.return_value = True
    mock_json_load.return_value = [
        {'name': 'Default 1', 'filters': {'page': 1}, 'watched': False},
        {'name': 'Default 2', 'filters': {'page': 2}, 'watched': False}
    ]
    mock_repo.find_by_name.return_value = None
    
    service.seed_defaults()
    
    assert mock_repo.create.call_count == 2
    mock_repo.create.assert_any_call('Default 1', {'page': 1}, False, ordering=0)
    mock_repo.create.assert_any_call('Default 2', {'page': 2}, False, ordering=1)
