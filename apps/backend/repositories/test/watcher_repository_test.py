import pytest
from unittest.mock import MagicMock, patch
from repositories.watcher_repository import WatcherRepository

@pytest.fixture
def mock_db():
    mock = MagicMock()
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = None
    return mock

@patch('repositories.watcher_repository.WatcherRepository.get_db')
@patch('repositories.watcher_repository.generate_config_view_sql')
def test_get_watcher_stats_from_view(mock_generate_sql, mock_get_db, mock_db):
    repo = WatcherRepository()
    mock_get_db.return_value = mock_db
    
    # Mock data
    config_ids = [1, 2]
    configs = [
        (1, '{"filter": "a"}'),
        (2, '{"filter": "b"}')
    ]
    
    # Setup mocks
    mock_db.fetchAll.side_effect = [
        configs, # First call: fetch configs
        # Second call: fetch union results
        [
            (1, '2023-01-01'),
            (1, '2023-01-02'),
            (2, '2023-01-03')
        ]
    ]
    
    mock_generate_sql.side_effect = [
        ("CREATE VIEW v1 AS ...", "v1"),
        ("CREATE VIEW v2 AS ...", "v2")
    ]
    
    # Execute
    results = repo.get_watcher_stats_from_view(config_ids)
    
    # Verify
    assert len(results) == 3
    assert results[0] == (1, '2023-01-01')
    
    # Verify DB calls
    assert mock_db.executeAndCommit.call_count == 2 # 2 view creations
    assert mock_db.fetchAll.call_count == 2
    
    # Verify generated SQL was used
    union_query = mock_db.fetchAll.call_args_list[1][0][0]
    assert "SELECT config_id, job_created FROM v1" in union_query
    assert "SELECT config_id, job_created FROM v2" in union_query
    assert "UNION ALL" in union_query

@patch('repositories.watcher_repository.WatcherRepository.get_db')
def test_get_watcher_stats_empty_ids(mock_get_db):
    repo = WatcherRepository()
    results = repo.get_watcher_stats_from_view([])
    assert results == []
    mock_get_db.assert_not_called()
