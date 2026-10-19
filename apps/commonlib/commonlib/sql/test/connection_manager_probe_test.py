"""Tests for MySQL probing and pool initialization in connection_manager."""
import pytest
from unittest.mock import patch, MagicMock
from commonlib.sql import connection_manager


class TestProbeMysql:
    def test_probe_success(self):
        with patch('commonlib.sql.connection_manager.mysqlConnector.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            connection_manager._probe_mysql("10.0.0.1")
            mock_conn.close.assert_called_once()

    def test_probe_e2e_no_database(self):
        with patch('commonlib.sql.connection_manager.mysqlConnector.connect') as mock_connect:
            mock_connect.return_value = MagicMock()
            connection_manager._probe_mysql("10.0.0.1", e2e_tests=True)
            assert mock_connect.call_args[1].get('database') is None

    def test_probe_failure(self):
        with patch('commonlib.sql.connection_manager.mysqlConnector.connect', side_effect=Exception("refused")):
            with pytest.raises(Exception):
                connection_manager._probe_mysql("10.0.0.1")


class TestInitPool:
    def test_pool_init_skips_if_initialized(self, mock_mysql_connect):
        connection_manager._pool_initialized = True
        connection_manager._init_pool()
        mock_mysql_connect.assert_not_called()

    def test_pool_init_creates_pool(self, mock_mysql_connect):
        connection_manager._init_pool()
        assert connection_manager._pool_initialized is True
