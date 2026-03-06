"""Tests for connection_manager module."""
import pytest
from unittest.mock import patch, MagicMock, call
from commonlib.sql import connection_manager


@pytest.fixture(autouse=True)
def mock_mysql_connect():
    """Mock the mysqlConnector.connect to avoid real DB connection."""
    with patch('commonlib.sql.connection_manager.mysqlConnector.connect') as mock_connect:
        mock_connect.return_value = MagicMock()

        # Reset the pool state before each test
        connection_manager._pool_initialized = False
        yield mock_connect
        connection_manager._pool_initialized = False


class TestGetConnection:
    """Tests for get_connection function."""

    def test_get_connection_returns_connection(self):
        """Should return a MySQL connection object."""
        conn = connection_manager.get_connection()
        assert conn is not None

    def test_pool_initialized_once(self, mock_mysql_connect):
        """Pool should only be created once across multiple calls."""
        connection_manager.get_connection()
        connection_manager.get_connection()
        # First call: pool init + get from pool. Second call: only get from pool.
        assert mock_mysql_connect.call_count == 3

    def test_get_connection_gets_from_pool(self, mock_mysql_connect):
        """Second call should get from pool without host/user params."""
        connection_manager.get_connection()
        second_call_kwargs = mock_mysql_connect.call_args_list[1][1]
        assert second_call_kwargs == {'pool_name': 'jobsPool'}

    def test_e2e_tests_connects_without_database(self, mock_mysql_connect):
        """E2E mode should not pass database parameter."""
        connection_manager.get_connection(e2e_tests=True)
        init_call_kwargs = mock_mysql_connect.call_args_list[0][1]
        assert init_call_kwargs.get('database') is None


class TestGetConnectionLegacy:
    """Tests for backward compatible getConnection function."""

    def test_getConnection_returns_connection(self):
        """Should return a MySQL connection object."""
        conn = connection_manager.getConnection()
        assert conn is not None

    def test_getConnection_delegates_to_get_connection(self, mock_mysql_connect):
        """Should call through to get_connection."""
        connection_manager.getConnection(e2eTests=True)
        init_call_kwargs = mock_mysql_connect.call_args_list[0][1]
        assert init_call_kwargs.get('database') is None
