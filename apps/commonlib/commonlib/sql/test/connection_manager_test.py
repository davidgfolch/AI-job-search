"""Tests for connection_manager module."""
import pytest
from commonlib.sql.connection_manager import get_connection, getConnection


class TestGetConnection:
    """Tests for get_connection function."""

    def test_get_connection_returns_connection(self):
        """Should return a MySQL connection object."""
        conn = get_connection()
        assert conn is not None
        assert hasattr(conn, 'is_connected')

    def test_get_connection_uses_pool(self):
        """Should use connection pooling."""
        conn1 = get_connection()
        conn2 = get_connection()
        # Both should come from same pool
        assert conn1.pool_name == conn2.pool_name == 'jobsPool'


class TestGetConnectionLegacy:
    """Tests for backward compatible getConnection function."""

    def test_getConnection_returns_connection(self):
        """Should return a MySQL connection object."""
        conn = getConnection()
        assert conn is not None

    def test_getConnection_uses_pool(self):
        """Should use connection pooling."""
        conn = getConnection()
        assert conn.pool_name == 'jobsPool'
