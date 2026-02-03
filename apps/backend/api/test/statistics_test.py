import pytest
from unittest.mock import patch

@patch('services.statistics_service.StatisticsService.get_history_stats')
def test_get_history_stats(mock_get_history, client):
    mock_data = [{"dateCreated": "2023-01-01", "applied": 5, "discarded": 3}]
    mock_get_history.return_value = mock_data
    response = client.get("/api/statistics/history")
    assert response.status_code == 200
    assert response.json() == mock_data

@patch('services.statistics_service.StatisticsService.get_sources_by_date')
def test_get_sources_by_date(mock_get_sources, client):
    mock_data = [{"dateCreated": "2023-01-01", "source": "LinkedIn", "total": 10}]
    mock_get_sources.return_value = mock_data
    response = client.get("/api/statistics/sources-date")
    assert response.status_code == 200
    assert response.json() == mock_data

@patch('services.statistics_service.StatisticsService.get_sources_by_hour')
def test_get_sources_by_hour(mock_get_sources, client):
    mock_data = [{"hour": 10, "source": "LinkedIn", "total": 5}]
    mock_get_sources.return_value = mock_data
    response = client.get("/api/statistics/sources-hour")
    assert response.status_code == 200
    assert response.json() == mock_data

@patch('services.statistics_service.StatisticsService.get_filter_configuration_stats')
def test_get_filter_config_stats(mock_get_stats, client):
    mock_data = [{"name": "Config 1", "count": 42}, {"name": "Config 2", "count": 15}]
    mock_get_stats.return_value = mock_data
    response = client.get("/api/statistics/filter-configs")
    assert response.status_code == 200
    assert response.json() == mock_data
