import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from repositories.snapshots_repository import SnapshotsRepository


@pytest.fixture
def mock_connection():
    with patch("repositories.snapshots_repository.getConnection") as mock:
        yield mock


def test_get_history_stats_df(mock_connection):
    repo = SnapshotsRepository()
    mock_df = pd.DataFrame(
        {
            "dateCreated": ["2023-01-01"],
            "applied": [1],
            "discarded": [0],
            "interview": [0],
        }
    )

    with patch("pandas.read_sql", return_value=mock_df):
        result = repo.get_history_stats_df()

    assert not result.empty


def test_get_history_stats_df_with_dates(mock_connection):
    repo = SnapshotsRepository()
    mock_df = pd.DataFrame(
        {"dateCreated": ["2023-01-01"], "applied": [1], "discarded": [0], "interview": [0]}
    )

    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        result = repo.get_history_stats_df(start_date="2023-01-01", end_date="2023-01-31")

    assert not result.empty
    query = mock_read.call_args[0][0]
    assert " WHERE " in query
    params = mock_read.call_args[1]["params"]
    assert params == ["2023-01-01", "2023-01-31"]


def test_get_snapshot_count_by_reason(mock_connection):
    repo = SnapshotsRepository()
    mock_df = pd.DataFrame({"snapshot_reason": ["DELETED"], "count": [10]})

    with patch("pandas.read_sql", return_value=mock_df):
        result = repo.get_snapshot_count_by_reason()

    assert not result.empty


def test_get_sources_by_date_df(mock_connection):
    repo = SnapshotsRepository()
    mock_df = pd.DataFrame({"dateCreated": ["2023-01-01"], "total": [3], "source": ["linkedin"]})

    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        result = repo.get_sources_by_date_df()

    assert not result.empty
    query = mock_read.call_args[0][0]
    assert "date(snapshot_at)" in query
    assert " WHERE " not in query


def test_get_sources_by_date_df_with_dates(mock_connection):
    repo = SnapshotsRepository()
    mock_df = pd.DataFrame({"dateCreated": ["2023-01-01"], "total": [3], "source": ["linkedin"]})

    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        result = repo.get_sources_by_date_df(start_date="2023-01-01", end_date="2023-01-31")

    assert not result.empty
    query = mock_read.call_args[0][0]
    assert " WHERE " in query
    params = mock_read.call_args[1]["params"]
    assert params == ["2023-01-01", "2023-01-31"]


def test_get_sources_by_hour_df(mock_connection):
    repo = SnapshotsRepository()
    mock_df = pd.DataFrame({"hour": [9], "source": ["linkedin"], "total": [2]})

    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        result = repo.get_sources_by_hour_df(start_date="2023-01-01")

    assert not result.empty
    query = mock_read.call_args[0][0]
    assert "HOUR(snapshot_at)" in query
    assert " WHERE " in query


def test_get_sources_by_hour_df_no_dates(mock_connection):
    repo = SnapshotsRepository()
    mock_df = pd.DataFrame(columns=["hour", "source", "total"])

    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        result = repo.get_sources_by_hour_df()

    assert result.empty
    query = mock_read.call_args[0][0]
    assert " WHERE " not in query


def test_get_sources_by_weekday_df(mock_connection):
    repo = SnapshotsRepository()
    mock_df = pd.DataFrame({"weekday": [2], "source": ["linkedin"], "total": [5]})

    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        result = repo.get_sources_by_weekday_df(end_date="2023-01-31")

    assert not result.empty
    query = mock_read.call_args[0][0]
    assert "DAYOFWEEK(snapshot_at)" in query
    assert " WHERE " in query


def test_get_sources_by_weekday_df_no_dates(mock_connection):
    repo = SnapshotsRepository()
    mock_df = pd.DataFrame(columns=["weekday", "source", "total"])

    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        result = repo.get_sources_by_weekday_df()

    assert result.empty
    query = mock_read.call_args[0][0]
    assert " WHERE " not in query


def test_get_snapshot_count_by_platform(mock_connection):
    repo = SnapshotsRepository()
    mock_df = pd.DataFrame({"platform": ["linkedin"], "count": [10]})

    with patch("pandas.read_sql", return_value=mock_df):
        result = repo.get_snapshot_count_by_platform()

    assert not result.empty
