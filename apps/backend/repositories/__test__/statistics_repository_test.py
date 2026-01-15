import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from repositories.statistics_repository import StatisticsRepository

@patch('repositories.statistics_repository.getConnection')
@patch('repositories.statistics_repository.pd.read_sql')
def test_get_history_stats_df(mock_read_sql, mock_get_conn):
    # Setup
    mock_conn = MagicMock()
    mock_get_conn.return_value = mock_conn
    
    expected_df = pd.DataFrame({'dateCreated': ['2023-01-01'], 'applied': [1]})
    mock_read_sql.return_value = expected_df
    
    repo = StatisticsRepository()
    
    # Act
    result = repo.get_history_stats_df()
    
    # Assert
    mock_get_conn.assert_called_once()
    mock_read_sql.assert_called_once()
    assert result.equals(expected_df)
    # Verify query structure (basics)
    query_arg = mock_read_sql.call_args[0][0]
    assert "SELECT" in query_arg
    assert "FROM jobs" in query_arg
    assert "GROUP BY dateCreated" in query_arg

@patch('repositories.statistics_repository.getConnection')
@patch('repositories.statistics_repository.pd.read_sql')
def test_get_sources_by_date_df(mock_read_sql, mock_get_conn):
    # Setup
    mock_conn = MagicMock()
    mock_get_conn.return_value = mock_conn
    mock_read_sql.return_value = pd.DataFrame()
    
    repo = StatisticsRepository()
    repo.get_sources_by_date_df()
    
    mock_read_sql.assert_called_once()
    query_arg = mock_read_sql.call_args[0][0]
    assert "SELECT" in query_arg
    assert "web_page as source" in query_arg

@patch('repositories.statistics_repository.getConnection')
@patch('repositories.statistics_repository.pd.read_sql')
def test_get_sources_by_hour_df(mock_read_sql, mock_get_conn):
    # Setup
    mock_conn = MagicMock()
    mock_get_conn.return_value = mock_conn
    mock_read_sql.return_value = pd.DataFrame()
    
    repo = StatisticsRepository()
    repo.get_sources_by_hour_df()
    
    mock_read_sql.assert_called_once()
    query_arg = mock_read_sql.call_args[0][0]
    assert "SELECT" in query_arg
    assert "HOUR(created)" in query_arg
