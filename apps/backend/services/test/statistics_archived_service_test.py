import pytest
from unittest.mock import MagicMock
import pandas as pd
from services.statistics_archived_service import StatisticsArchivedService
from repositories.snapshots_repository import SnapshotsRepository
from repositories.statistics_repository import StatisticsRepository
from repositories.combinedStatsRepository import CombinedStatsRepository


@pytest.fixture
def mock_snapshots_repo():
    return MagicMock(spec=SnapshotsRepository)


@pytest.fixture
def mock_stats_repo():
    return MagicMock(spec=StatisticsRepository)


@pytest.fixture
def mock_combined_repo():
    return MagicMock(spec=CombinedStatsRepository)


@pytest.fixture
def service(mock_snapshots_repo, mock_stats_repo, mock_combined_repo):
    return StatisticsArchivedService(
        snapshots_repo=mock_snapshots_repo,
        stats_repo=mock_stats_repo,
        combined_repo=mock_combined_repo,
    )


def test_get_archived_history_stats(service, mock_snapshots_repo):
    mock_df = pd.DataFrame(
        {
            "dateCreated": ["2023-01-01"],
            "applied": [1],
            "discarded": [0],
            "interview": [0],
        }
    )
    mock_snapshots_repo.get_history_stats_df.return_value = mock_df

    result = service.get_archived_history_stats()

    assert len(result) == 1
    assert result[0]["applied"] == 1


def test_get_archived_history_stats_empty(service, mock_snapshots_repo):
    mock_snapshots_repo.get_history_stats_df.return_value = pd.DataFrame()

    result = service.get_archived_history_stats()

    assert result == []


def test_get_archived_sources_by_date(service, mock_snapshots_repo):
    mock_df = pd.DataFrame({"dateCreated": ["2023-01-01"], "total": [3], "source": ["linkedin"]})
    mock_snapshots_repo.get_sources_by_date_df.return_value = mock_df

    result = service.get_archived_sources_by_date(start_date="2023-01-01")

    assert len(result) == 1
    mock_snapshots_repo.get_sources_by_date_df.assert_called_once_with(
        start_date="2023-01-01", end_date=None
    )


def test_get_archived_sources_by_hour(service, mock_snapshots_repo):
    mock_df = pd.DataFrame({"hour": [9], "source": ["linkedin"], "total": [2]})
    mock_snapshots_repo.get_sources_by_hour_df.return_value = mock_df

    result = service.get_archived_sources_by_hour()

    assert len(result) == 1


def test_get_archived_sources_by_weekday(service, mock_snapshots_repo):
    mock_df = pd.DataFrame({"weekday": [2], "source": ["linkedin"], "total": [5]})
    mock_snapshots_repo.get_sources_by_weekday_df.return_value = mock_df

    result = service.get_archived_sources_by_weekday()

    assert len(result) == 1


def test_get_combined_history_stats(service, mock_combined_repo):
    mock_df = pd.DataFrame(
        {"dateCreated": ["2023-01-01", "2023-01-02"], "discarded": [1, 2], "interview": [1, 1]}
    )
    mock_combined_repo.get_combined_history_stats_df.return_value = mock_df

    result = service.get_combined_history_stats()

    assert len(result) == 2
    assert result[0]["discarded_cumulative"] == 1
    assert result[1]["discarded_cumulative"] == 3
    assert result[1]["interview_cumulative"] == 2


def test_get_combined_history_stats_empty(service, mock_combined_repo):
    mock_combined_repo.get_combined_history_stats_df.return_value = pd.DataFrame()

    result = service.get_combined_history_stats()

    assert result == []


def test_get_combined_sources_by_date(service, mock_combined_repo):
    mock_df = pd.DataFrame({"dateCreated": ["2023-01-01"], "total": [3], "source": ["linkedin"]})
    mock_combined_repo.get_combined_sources_by_date_df.return_value = mock_df

    result = service.get_combined_sources_by_date()

    assert len(result) == 1


def test_get_combined_sources_by_hour(service, mock_combined_repo):
    mock_df = pd.DataFrame({"hour": [9], "source": ["linkedin"], "total": [2]})
    mock_combined_repo.get_combined_sources_by_hour_df.return_value = mock_df

    result = service.get_combined_sources_by_hour()

    assert len(result) == 1


def test_get_combined_sources_by_weekday(service, mock_combined_repo):
    mock_df = pd.DataFrame({"weekday": [2], "source": ["linkedin"], "total": [5]})
    mock_combined_repo.get_combined_sources_by_weekday_df.return_value = mock_df

    result = service.get_combined_sources_by_weekday()

    assert len(result) == 1


def test_get_snapshots_by_reason(service, mock_snapshots_repo):
    mock_df = pd.DataFrame(
        {"snapshot_reason": ["DELETED", "APPLIED"], "count": [10, 5]}
    )
    mock_snapshots_repo.get_snapshot_count_by_reason.return_value = mock_df

    result = service.get_snapshots_by_reason()

    assert len(result) == 2


def test_get_snapshots_by_platform(service, mock_snapshots_repo):
    mock_df = pd.DataFrame({"platform": ["linkedin"], "count": [10]})
    mock_snapshots_repo.get_snapshot_count_by_platform.return_value = mock_df

    result = service.get_snapshots_by_platform()

    assert len(result) == 1
