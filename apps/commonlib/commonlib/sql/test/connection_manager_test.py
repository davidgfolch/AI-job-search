"""Tests for connection_manager module."""
import pytest
from unittest.mock import patch, MagicMock
from commonlib.sql import connection_manager


@pytest.fixture(autouse=True)
def mock_mysql_connect():
    """Mock the mysqlConnector.connect to avoid real DB connection."""
    with patch('commonlib.sql.connection_manager.mysqlConnector.connect') as mock_connect:
        def connect_side_effect(*args, **kwargs):
            mock_instance = MagicMock()
            mock_instance.pool_name = kwargs.get('pool_name')
            return mock_instance
            
        mock_connect.side_effect = connect_side_effect
        
        # Reset the global connection state before each test
        connection_manager._conn = None
        yield mock_connect
        # Clean up after test
        connection_manager._conn = None


class TestGetConnection:
    """Tests for get_connection function."""

    def test_get_connection_returns_connection(self):
        """Should return a MySQL connection object."""
        conn = connection_manager.get_connection()
        assert conn is not None
        assert hasattr(conn, 'is_connected')

    def test_get_connection_uses_pool(self):
        """Should use connection pooling."""
        conn1 = connection_manager.get_connection()
        conn2 = connection_manager.get_connection()
        # Both should come from same pool
        assert conn1.pool_name == conn2.pool_name == 'jobsPool'


class TestGetConnectionLegacy:
    """Tests for backward compatible getConnection function."""

    def test_getConnection_returns_connection(self):
        """Should return a MySQL connection object."""
        conn = connection_manager.getConnection()
        assert conn is not None

    def test_getConnection_uses_pool(self):
        """Should use connection pooling."""
        conn = connection_manager.getConnection()
        assert conn.pool_name == 'jobsPool'
