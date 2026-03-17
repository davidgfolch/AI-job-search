import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from repositories.combinedStatsRepository import CombinedStatsRepository


def test_get_combined_history_stats_df():
    repo = CombinedStatsRepository()
    mock_df = pd.DataFrame(
        {
            "dateCreated": ["2023-01-01"],
            "applied": [1],
            "discarded": [0],
            "interview": [0],
        }
    )

    with patch("repositories.combinedStatsRepository.getConnection") as mock_conn:
        mock_conn.return_value.__enter__.return_value = MagicMock()
        with patch("pandas.read_sql", return_value=mock_df):
            result = repo.get_combined_history_stats_df()

    assert not result.empty


def test_get_combined_history_stats_df_with_dates():
    repo = CombinedStatsRepository()
    mock_df = pd.DataFrame(
        {
            "dateCreated": ["2023-01-01"],
            "applied": [1],
            "discarded": [0],
            "interview": [0],
        }
    )

    with patch("repositories.combinedStatsRepository.getConnection") as mock_conn:
        mock_conn.return_value.__enter__.return_value = MagicMock()
        with patch("pandas.read_sql", return_value=mock_df) as mock_read_sql:
            repo.get_combined_history_stats_df(start_date="2023-01-01", end_date="2023-12-31")
            call_args = mock_read_sql.call_args
            sql_query = call_args[0][0]
            assert "FROM jobs" in sql_query
            assert "WHERE created >=" in sql_query
            assert "FROM job_snapshots" in sql_query
            assert "WHERE original_created_at >=" in sql_query


def test_get_combined_sources_by_date_df_with_dates():
    repo = CombinedStatsRepository()
    mock_df = pd.DataFrame(
        {
            "dateCreated": ["2023-01-01"],
            "source": ["linkedin"],
            "total": [10],
        }
    )

    with patch("repositories.combinedStatsRepository.getConnection") as mock_conn:
        mock_conn.return_value.__enter__.return_value = MagicMock()
        with patch("pandas.read_sql", return_value=mock_df) as mock_read_sql:
            repo.get_combined_sources_by_date_df(start_date="2023-01-01", end_date="2023-12-31")
            call_args = mock_read_sql.call_args
            sql_query = call_args[0][0]
            assert "FROM jobs" in sql_query
            assert "CAST(%s AS DATE)" in sql_query
            assert "FROM job_snapshots" in sql_query


def test_get_combined_sources_by_hour_df_with_dates():
    repo = CombinedStatsRepository()
    mock_df = pd.DataFrame(
        {
            "hour": [10],
            "source": ["linkedin"],
            "total": [5],
        }
    )

    with patch("repositories.combinedStatsRepository.getConnection") as mock_conn:
        mock_conn.return_value.__enter__.return_value = MagicMock()
        with patch("pandas.read_sql", return_value=mock_df) as mock_read_sql:
            repo.get_combined_sources_by_hour_df(start_date="2023-01-01", end_date="2023-12-31")
            call_args = mock_read_sql.call_args
            sql_query = call_args[0][0]
            assert "FROM jobs" in sql_query
            assert "WHERE created >=" in sql_query
            assert "FROM job_snapshots" in sql_query
            assert "WHERE original_created_at >=" in sql_query


def test_get_combined_sources_by_weekday_df_with_dates():
    repo = CombinedStatsRepository()
    mock_df = pd.DataFrame(
        {
            "weekday": [1],
            "source": ["linkedin"],
            "total": [5],
        }
    )

    with patch("repositories.combinedStatsRepository.getConnection") as mock_conn:
        mock_conn.return_value.__enter__.return_value = MagicMock()
        with patch("pandas.read_sql", return_value=mock_df) as mock_read_sql:
            repo.get_combined_sources_by_weekday_df(start_date="2023-01-01", end_date="2023-12-31")
            call_args = mock_read_sql.call_args
            sql_query = call_args[0][0]
            assert "FROM jobs" in sql_query
            assert "WHERE created >=" in sql_query
            assert "FROM job_snapshots" in sql_query
            assert "WHERE original_created_at >=" in sql_query
