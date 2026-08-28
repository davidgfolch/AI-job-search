"""Tests for connection_manager module."""
import os
import queue
import pytest
from unittest.mock import patch, MagicMock
from commonlib.sql import connection_manager


@pytest.fixture(autouse=True)
def mock_mysql_connect():
    with patch('commonlib.sql.connection_manager.mysqlConnector.connect') as mock_connect, \
         patch.dict(os.environ, {'COMMONLIB_DB_HOST': '127.0.0.1'}, clear=False):
        mock_connect.return_value = MagicMock()
        connection_manager._pool_initialized = False
        yield mock_connect
        connection_manager._pool_initialized = False


@pytest.mark.parametrize("range_str,expected", [
    ("192.168.0.1-192.168.0.3", ["192.168.0.1", "192.168.0.2", "192.168.0.3"]),
    ("192.168.0.10-12", ["192.168.0.10", "192.168.0.11", "192.168.0.12"]),
    ("10.0.0.1-10.0.0.1", ["10.0.0.1"]),
])
def test_parse_ip_range(range_str, expected):
    assert connection_manager._parse_ip_range(range_str) == expected


def test_parse_ip_range_three_octets():
    result = connection_manager._parse_ip_range("192.168.0.10-192.168.0.250")
    assert result[0] == "192.168.0.10"
    assert result[-1] == "192.168.0.250"


def test_parse_ip_range_diff_prefix():
    assert len(connection_manager._parse_ip_range("10.1.2.3-3.4.5")) > 0
    assert len(connection_manager._parse_ip_range("192.168.0.10-1.20")) > 0


def test_parse_ip_range_end_before_start_raises():
    with pytest.raises(ValueError, match="Range end"):
        connection_manager._parse_ip_range("192.168.0.50-192.168.0.10")


def test_parse_host_targets():
    assert connection_manager._parse_host_targets("127.0.0.1") == ["127.0.0.1"]
    assert connection_manager._parse_host_targets("10.0.0.1,10.0.0.2") == ["10.0.0.1", "10.0.0.2"]
    assert len(connection_manager._parse_host_targets("10.0.0.1-3")) == 3
    assert "192.168.1.1" in connection_manager._parse_host_targets("192.168.1.0/30")


def test_parse_host_targets_cleanup():
    assert connection_manager._parse_host_targets("10.0.0.1,,10.0.0.2") == ["10.0.0.1", "10.0.0.2"]
    assert connection_manager._parse_host_targets("  10.0.0.1  ,  10.0.0.2  ") == ["10.0.0.1", "10.0.0.2"]


class TestTryTargets:
    def test_small_range_first_host(self):
        with patch('commonlib.sql.connection_manager._probe_mysql'):
            assert connection_manager._try_targets(["10.0.0.1", "10.0.0.2"], False) == "10.0.0.1"

    def test_small_range_second_host(self):
        with patch('commonlib.sql.connection_manager._probe_mysql', side_effect=[Exception("fail"), None]):
            assert connection_manager._try_targets(["10.0.0.1", "10.0.0.2"], False) == "10.0.0.2"

    def test_small_range_none_reachable(self):
        with patch('commonlib.sql.connection_manager._probe_mysql', side_effect=Exception("fail")):
            assert connection_manager._try_targets(["10.0.0.1"], False) is None

    def test_large_range_uses_discovery(self):
        targets = [f"10.0.0.{i}" for i in range(15)]
        with patch('commonlib.network.mysql_discovery.discover_mysql_hosts', return_value=["10.0.0.1"]), \
             patch('commonlib.network.mysql_discovery.verify_mysql', return_value=True):
            assert connection_manager._try_targets(targets, False) == "10.0.0.1"

    def test_large_range_no_open_hosts(self):
        targets = [f"10.0.0.{i}" for i in range(15)]
        with patch('commonlib.network.mysql_discovery.discover_mysql_hosts', return_value=[]):
            assert connection_manager._try_targets(targets, False) is None

    def test_large_range_host_not_verified(self):
        targets = [f"10.0.0.{i}" for i in range(15)]
        with patch('commonlib.network.mysql_discovery.discover_mysql_hosts', return_value=["10.0.0.1"]), \
             patch('commonlib.network.mysql_discovery.verify_mysql', return_value=False):
            assert connection_manager._try_targets(targets, False) is None


class TestResolveDbHost:
    def test_resolve_with_configured_host(self):
        with patch.dict(os.environ, {'COMMONLIB_DB_HOST': '10.0.0.1'}), \
             patch('commonlib.sql.connection_manager._try_targets', return_value='10.0.0.1'):
            assert connection_manager._resolve_db_host() == '10.0.0.1'

    def test_resolve_fallback_to_localhost(self):
        with patch.dict(os.environ, {'COMMONLIB_DB_HOST': ''}), \
             patch('commonlib.sql.connection_manager._try_targets', return_value='127.0.0.1'):
            assert connection_manager._resolve_db_host() == '127.0.0.1'

    def test_resolve_fallback_to_lan_discovery(self):
        with patch.dict(os.environ, {'COMMONLIB_DB_HOST': ''}), \
             patch('commonlib.sql.connection_manager._try_targets', return_value=None), \
             patch('commonlib.network.mysql_discovery.auto_discover_host', return_value='192.168.1.100'):
            assert connection_manager._resolve_db_host() == '192.168.1.100'

    def test_resolve_no_host_raises(self):
        with patch.dict(os.environ, {'COMMONLIB_DB_HOST': ''}), \
             patch('commonlib.sql.connection_manager._try_targets', return_value=None), \
             patch('commonlib.network.mysql_discovery.auto_discover_host', return_value=None):
            with pytest.raises(ConnectionError, match="Could not connect"):
                connection_manager._resolve_db_host()

    def test_resolve_comma_separated_groups(self):
        with patch.dict(os.environ, {'COMMONLIB_DB_HOST': '10.0.0.1,10.0.0.2'}), \
             patch('commonlib.sql.connection_manager._try_targets', side_effect=[None, '10.0.0.2']):
            assert connection_manager._resolve_db_host() == '10.0.0.2'


class TestGetConnection:
    def test_get_connection_returns_connection(self):
        assert connection_manager.get_connection() is not None

    def test_pool_initialized_once(self, mock_mysql_connect):
        connection_manager.get_connection()
        connection_manager.get_connection()
        assert mock_mysql_connect.call_count == 4

    def test_get_connection_gets_from_pool(self, mock_mysql_connect):
        connection_manager.get_connection()
        assert mock_mysql_connect.call_args_list[2][1] == {'pool_name': 'jobsPool'}

    def test_e2e_tests_connects_without_database(self, mock_mysql_connect):
        connection_manager.get_connection(e2e_tests=True)
        assert mock_mysql_connect.call_args_list[0][1].get('database') is None

    def test_get_connection_retry_on_pool_exhausted(self, mock_mysql_connect):
        call_count = [0]
        def side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise queue.Empty("Pool exhausted")
            return MagicMock()
        mock_mysql_connect.side_effect = side_effect
        connection_manager._pool_initialized = True
        assert connection_manager.get_connection() is not None

    def test_get_connection_all_retries_fail_raises(self, mock_mysql_connect):
        mock_mysql_connect.side_effect = queue.Empty("Pool exhausted")
        connection_manager._pool_initialized = True
        with pytest.raises(queue.Empty, match="All pool connections"):
            connection_manager.get_connection()

    @patch('commonlib.sql.connection_manager.DEBUG', True)
    def test_get_connection_debug_mode(self, mock_mysql_connect):
        assert connection_manager.get_connection() is not None

    def test_get_connection_legacy_delegates(self, mock_mysql_connect):
        connection_manager.getConnection(e2eTests=True)
        assert mock_mysql_connect.call_args_list[0][1].get('database') is None


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
