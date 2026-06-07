"""Tests for connection_manager module."""
import os
import pytest
from unittest.mock import patch, MagicMock, call
from commonlib.sql import connection_manager


@pytest.fixture(autouse=True)
def mock_mysql_connect():
    """Mock the mysqlConnector.connect to avoid real DB connection.
    Also resets COMMONLIB_DB_HOST so tests use the default 127.0.0.1 path."""
    with patch('commonlib.sql.connection_manager.mysqlConnector.connect') as mock_connect, \
         patch.dict(os.environ, {'COMMONLIB_DB_HOST': '127.0.0.1'}, clear=False):
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
        # First get_connection: probe (1) + pool init (1) + get from pool (1).
        # Second get_connection: get from pool (1).
        assert mock_mysql_connect.call_count == 4

    def test_get_connection_gets_from_pool(self, mock_mysql_connect):
        """Third call (get from pool) should only pass pool_name."""
        connection_manager.get_connection()
        # Call 0: probe, Call 1: pool init, Call 2: get from pool
        pool_call_kwargs = mock_mysql_connect.call_args_list[2][1]
        assert pool_call_kwargs == {'pool_name': 'jobsPool'}

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
