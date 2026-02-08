import pytest
from unittest.mock import MagicMock, patch
from services.watcher_service import WatcherService
from datetime import datetime

@pytest.fixture
def mock_repo():
    return MagicMock()

def test_get_watcher_stats(mock_repo):
    with patch('services.watcher_service.WatcherRepository', return_value=mock_repo):
        service = WatcherService()
        
        # Mock repo response
        mock_repo.get_watcher_stats_from_view.return_value = [
            (1, datetime(2023, 1, 10)),
            (1, datetime(2023, 1, 15)),
            (2, datetime(2023, 1, 5))
        ]
        
        config_ids = [1, 2]
        cutoff_map = {
            1: "2023-01-12",
            2: "2023-01-01"
        }
        
        results = service.get_watcher_stats(config_ids, cutoff_map)
        
        # Verify
        assert results[1]["total"] == 2
        assert results[1]["new_items"] == 1 # Only 2023-01-15 is after 2023-01-12
        
        assert results[2]["total"] == 1
        assert results[2]["new_items"] == 1 # 2023-01-05 is after 2023-01-01

def test_get_watcher_stats_string_dates(mock_repo):
    with patch('services.watcher_service.WatcherRepository', return_value=mock_repo):
        service = WatcherService()
        
        # Mock repo response with strings (simulating some DB drivers or raw values)
        mock_repo.get_watcher_stats_from_view.return_value = [
            (1, "2023-01-10"),
            (1, "2023-01-15")
        ]
        
        config_ids = [1]
        cutoff_map = {1: "2023-01-12"}
        
        results = service.get_watcher_stats(config_ids, cutoff_map)
        
        assert results[1]["total"] == 2
        assert results[1]["new_items"] == 1

def test_get_watcher_stats_error_handling(mock_repo):
    with patch('services.watcher_service.WatcherRepository', return_value=mock_repo):
        service = WatcherService()
        
        mock_repo.get_watcher_stats_from_view.side_effect = Exception("DB Error")
        
        results = service.get_watcher_stats([1])
        
        # Should return default initialized structure (0s)
        assert results[1]["total"] == 0
        assert results[1]["new_items"] == 0

def test_get_watcher_stats_timezone_mismatch(mock_repo):
    """
    Test scenario:
    - Host/DB Time: UTC+1 (e.g., 10:00 Local is 09:00 UTC)
    - Request Cutoff: UTC (e.g., 09:00Z)
    
    If an item is created at 10:00 Local (09:00 UTC), and we ask for items since 09:00 UTC,
    it should technically be "not new" (or barely new, but let's say equal).
    
    Crucial case: 
    Item created 09:55 Local (08:55 UTC).
    Cutoff 09:00 UTC.
    Item (08:55 UTC) < Cutoff (09:00 UTC).
    Should NOT be new.
    
    Current Bug:
    "09:55" (String) > "09:00Z" (String).
    Result: New (False Positive).
    """
    with patch('services.watcher_service.WatcherRepository', return_value=mock_repo):
        service = WatcherService()
        
        # Mock repo response: Naive Local Time
        # created at 09:55 Local time.
        # If Host is UTC+1, this is 08:55 UTC.
        # Python datetime from DB is usually naive.
        db_time = datetime(2026, 2, 7, 9, 55, 0) # 09:55 naive
        
        mock_repo.get_watcher_stats_from_view.return_value = [
            (1, db_time)
        ]
        
        config_ids = [1]
        # Frontend sends UTC time for 10:00 Local -> 09:00 UTC
        cutoff_map = {
            1: "2026-02-07T09:00:00.000Z"
        }
        
        results = service.get_watcher_stats(config_ids, cutoff_map)
        
        # We expect 0 new items because 08:55 UTC < 09:00 UTC
        # The bug causes this assertion to fail (it returns 1)
        assert results[1]["new_items"] == 0

def test_get_watcher_stats_naive_local_input(mock_repo):
    """
    Test scenario:
    - Frontend sends Naive Local Time string (e.g., "2026-02-07T10:00:00")
    - Backend should interpret this as Local Time.
    """
    with patch('services.watcher_service.WatcherRepository', return_value=mock_repo):
        service = WatcherService()
        
        # Mock repo response: Naive Local Time (09:55)
        db_time = datetime(2026, 2, 7, 9, 55, 0) 
        
        mock_repo.get_watcher_stats_from_view.return_value = [
            (1, db_time)
        ]
        
        config_ids = [1]
        # Frontend sends Naive Local time "10:00:00"
        cutoff_map = {
            1: "2026-02-07T10:00:00"
        }
        
        results = service.get_watcher_stats(config_ids, cutoff_map)
        
        # 09:55 < 10:00 -> 0 new items
        assert results[1]["new_items"] == 0
        
        # Case 2: Cutoff is "09:00:00"
        cutoff_map_2 = {
            1: "2026-02-07T09:00:00"
        }
        results_2 = service.get_watcher_stats(config_ids, cutoff_map_2)
        # 09:55 > 09:00 -> 1 new item
        assert results_2[1]["new_items"] == 1
