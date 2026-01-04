import pytest
from unittest.mock import MagicMock
import pandas as pd
from services.statistics_service import StatisticsService
from repositories.statistics_repository import StatisticsRepository

@pytest.fixture
def mock_repo():
    return MagicMock(spec=StatisticsRepository)

@pytest.fixture
def service(mock_repo):
    return StatisticsService(repo=mock_repo)

def test_get_history_stats(service, mock_repo):
    # Mock data
    data = {
        'dateCreated': ['2023-01-01', '2023-01-02'],
        'applied': [1, 2],
        'discarded': [3, 4],
        'interview': [0, 1]
    }
    df = pd.DataFrame(data)
    mock_repo.get_history_stats_df.return_value = df

    # Call service
    result = service.get_history_stats()

    # Verify calls
    mock_repo.get_history_stats_df.assert_called_once()

    # Verify cumulative calculations
    assert len(result) == 2
    assert result[0]['discarded_cumulative'] == 3
    assert result[1]['discarded_cumulative'] == 7  # 3 + 4
    assert result[0]['interview_cumulative'] == 0
    assert result[1]['interview_cumulative'] == 1  # 0 + 1

def test_get_sources_by_date(service, mock_repo):
    data = {'dateCreated': [], 'total': [], 'source': []}
    mock_repo.get_sources_by_date_df.return_value = pd.DataFrame(data)
    
    service.get_sources_by_date()
    mock_repo.get_sources_by_date_df.assert_called_once()

def test_get_sources_by_hour(service, mock_repo):
    data = {'hour': [], 'source': [], 'total': []}
    mock_repo.get_sources_by_hour_df.return_value = pd.DataFrame(data)
    
    service.get_sources_by_hour()
    mock_repo.get_sources_by_hour_df.assert_called_once()
