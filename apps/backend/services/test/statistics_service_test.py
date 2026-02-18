import pytest
from unittest.mock import MagicMock
import pandas as pd
from services.statistics_service import StatisticsService
from repositories.statistics_repository import StatisticsRepository
from repositories.filter_configurations_repository import FilterConfigurationsRepository
from repositories.jobs_repository import JobsRepository


@pytest.fixture
def mock_repo():
    return MagicMock(spec=StatisticsRepository)


@pytest.fixture
def mock_filter_repo():
    return MagicMock(spec=FilterConfigurationsRepository)


@pytest.fixture
def mock_jobs_repo():
    return MagicMock(spec=JobsRepository)


@pytest.fixture
def service(mock_repo, mock_filter_repo, mock_jobs_repo):
    return StatisticsService(
        repo=mock_repo, filter_repo=mock_filter_repo, jobs_repo=mock_jobs_repo
    )


def test_get_history_stats(service, mock_repo):
    # Mock data
    data = {
        "dateCreated": ["2023-01-01", "2023-01-02"],
        "applied": [1, 2],
        "discarded": [3, 4],
        "interview": [0, 1],
    }
    df = pd.DataFrame(data)
    mock_repo.get_history_stats_df.return_value = df

    # Call service
    result = service.get_history_stats()

    # Verify calls
    mock_repo.get_history_stats_df.assert_called_once()

    # Verify cumulative calculations
    assert len(result) == 2
    assert result[0]["discarded_cumulative"] == 3
    assert result[1]["discarded_cumulative"] == 7  # 3 + 4
    assert result[0]["interview_cumulative"] == 0
    assert result[1]["interview_cumulative"] == 1  # 0 + 1


def test_get_sources_by_date(service, mock_repo):
    data = {"dateCreated": [], "total": [], "source": []}
    mock_repo.get_sources_by_date_df.return_value = pd.DataFrame(data)

    service.get_sources_by_date()
    mock_repo.get_sources_by_date_df.assert_called_once()


def test_get_sources_by_hour(service, mock_repo):
    data = {"hour": [], "source": [], "total": []}
    mock_repo.get_sources_by_hour_df.return_value = pd.DataFrame(data)

    service.get_sources_by_hour()
    mock_repo.get_sources_by_hour_df.assert_called_once()


def test_get_filter_configuration_stats_removes_boolean_filters(
    service, mock_filter_repo, mock_jobs_repo
):
    # Setup
    config = {
        "name": "Test Config",
        "statistics": True,
        "filters": {
            "search": "python",
            "status": "applied",
            "not_status": "discarded",
            "days_old": 7,
            "ignored": True,  # boolean filter
            "applied": True,  # boolean filter
        },
    }
    mock_filter_repo.find_all.return_value = [config]

    # Mock db context manager from jobs_repo
    mock_db = MagicMock()
    # Mock context manager return value
    mock_jobs_repo.get_db.return_value.__enter__.return_value = mock_db
    mock_jobs_repo._count_jobs.return_value = 10

    # Mock build_where to return something
    mock_jobs_repo.build_where.return_value = (["1=1"], [])

    # Execute
    result = service.get_filter_configuration_stats()

    # Assert
    assert len(result) == 1
    assert result[0]["count"] == 10

    # CRITICAL ASSERTION: Check that build_where was called with None for status, not_status and boolean_filters
    mock_jobs_repo.build_where.assert_called_once()

    # Get kwargs
    call_kwargs = mock_jobs_repo.build_where.call_args[1]

    # Check that boolean/stat filters are explicitly None
    assert call_kwargs.get("status") is None
    assert call_kwargs.get("not_status") is None
    assert call_kwargs.get("boolean_filters") is None

    # Check that other filters are preserved
    assert call_kwargs.get("search") == "python"
    assert call_kwargs.get("days_old") == 7


def test_get_history_stats_with_dates(service, mock_repo):
    df = pd.DataFrame(
        {
            "dateCreated": ["2023-01-01"],
            "applied": [1],
            "discarded": [0],
            "interview": [0],
        }
    )
    mock_repo.get_history_stats_df.return_value = df

    service.get_history_stats(start_date="2023-01-01", end_date="2023-12-31")

    mock_repo.get_history_stats_df.assert_called_once_with(
        start_date="2023-01-01", end_date="2023-12-31"
    )


def test_get_filter_configuration_stats_with_dates(
    service, mock_filter_repo, mock_jobs_repo
):
    mock_filter_repo.find_all.return_value = [
        {"name": "Test", "statistics": True, "filters": {}}
    ]
    mock_db = MagicMock()
    mock_jobs_repo.get_db.return_value.__enter__.return_value = mock_db
    mock_jobs_repo._count_jobs.return_value = 5
    mock_jobs_repo.build_where.return_value = (["1=1"], [])

    service.get_filter_configuration_stats(
        start_date="2023-01-01", end_date="2023-12-31"
    )

    call_kwargs = mock_jobs_repo.build_where.call_args[1]
    assert call_kwargs.get("start_date") == "2023-01-01"
    assert call_kwargs.get("end_date") == "2023-12-31"
