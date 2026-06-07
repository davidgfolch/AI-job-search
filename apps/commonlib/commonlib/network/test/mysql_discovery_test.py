from unittest.mock import patch, MagicMock
import pytest
from commonlib.network.mysql_discovery import (
    get_local_subnets, _scan_port, discover_mysql_hosts,
    verify_mysql, auto_discover_host,
)


class TestGetLocalSubnets:
    def test_returns_subnets(self):
        subnets = get_local_subnets()
        assert isinstance(subnets, list)
        if subnets:
            assert all('/' in s for s in subnets)

    @patch('commonlib.network.mysql_discovery.socket.socket')
    def test_returns_empty_on_failure(self, mock_socket_class):
        inst = MagicMock()
        inst.connect.side_effect = Exception("no network")
        mock_socket_class.return_value = inst
        assert get_local_subnets() == []


class TestScanPort:
    @patch('commonlib.network.mysql_discovery.socket.socket')
    def test_port_open(self, mock_socket):
        inst = MagicMock()
        inst.connect_ex.return_value = 0
        mock_socket.return_value = inst
        assert _scan_port('192.168.1.1', 3306, 0.5) is True

    @patch('commonlib.network.mysql_discovery.socket.socket')
    def test_port_closed(self, mock_socket):
        inst = MagicMock()
        inst.connect_ex.return_value = 1
        mock_socket.return_value = inst
        assert _scan_port('192.168.1.1', 3306, 0.5) is False

    @patch('commonlib.network.mysql_discovery.socket.socket')
    def test_exception(self, mock_socket_class):
        inst = MagicMock()
        inst.connect_ex.side_effect = OSError("connection error")
        mock_socket_class.return_value = inst
        assert _scan_port('192.168.1.1', 3306, 0.5) is False


class TestDiscoverMySQLHosts:
    @patch('commonlib.network.mysql_discovery._scan_hosts')
    def test_with_targets(self, mock_scan):
        mock_scan.return_value = ['192.168.1.10', '192.168.1.20']
        result = discover_mysql_hosts(targets=['192.168.1.10', '192.168.1.20'])
        assert result == ['192.168.1.10', '192.168.1.20']
        mock_scan.assert_called_once_with(['192.168.1.10', '192.168.1.20'], 3306, 0.5)

    @patch('commonlib.network.mysql_discovery.get_local_subnets')
    @patch('commonlib.network.mysql_discovery._scan_hosts')
    def test_with_subnets(self, mock_scan, mock_subnets):
        mock_subnets.return_value = ['192.168.1.0/24']
        mock_scan.return_value = ['192.168.1.5']
        result = discover_mysql_hosts(subnets=['10.0.0.0/24'])
        assert result == ['192.168.1.5']

    @patch('commonlib.network.mysql_discovery.get_local_subnets')
    @patch('commonlib.network.mysql_discovery._scan_hosts')
    def test_auto_subnets(self, mock_scan, mock_subnets):
        mock_subnets.return_value = ['192.168.1.0/24']
        mock_scan.return_value = ['192.168.1.5']
        result = discover_mysql_hosts()
        mock_subnets.assert_called_once()
        assert result == ['192.168.1.5']

    @patch('commonlib.network.mysql_discovery._scan_hosts')
    def test_no_targets_no_subnets(self, mock_scan):
        mock_scan.return_value = []
        with patch('commonlib.network.mysql_discovery.get_local_subnets', return_value=[]):
            result = discover_mysql_hosts()
        assert result == []


class TestVerifyMySQL:
    @patch('mysql.connector.connect')
    def test_verified(self, mock_connect):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = (1,)
        conn.cursor.return_value = cursor
        mock_connect.return_value = conn
        assert verify_mysql('192.168.1.10') is True

    @patch('mysql.connector.connect')
    def test_db_not_found(self, mock_connect):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = (0,)
        conn.cursor.return_value = cursor
        mock_connect.return_value = conn
        assert verify_mysql('192.168.1.10') is False

    @patch('mysql.connector.connect')
    def test_connection_failure(self, mock_connect):
        mock_connect.side_effect = Exception("connection refused")
        assert verify_mysql('192.168.1.10') is False


class TestAutoDiscoverHost:
    @patch('commonlib.network.mysql_discovery.discover_mysql_hosts')
    @patch('commonlib.network.mysql_discovery.verify_mysql')
    def test_found(self, mock_verify, mock_discover):
        mock_discover.return_value = ['192.168.1.10', '192.168.1.20']
        mock_verify.side_effect = [False, True]
        assert auto_discover_host() == '192.168.1.20'

    @patch('commonlib.network.mysql_discovery.discover_mysql_hosts')
    def test_no_candidates(self, mock_discover):
        mock_discover.return_value = []
        assert auto_discover_host() is None

    @patch('commonlib.network.mysql_discovery.discover_mysql_hosts')
    @patch('commonlib.network.mysql_discovery.verify_mysql')
    def test_no_verified(self, mock_verify, mock_discover):
        mock_discover.return_value = ['192.168.1.10']
        mock_verify.return_value = False
        assert auto_discover_host() is None

    @patch('commonlib.network.mysql_discovery.discover_mysql_hosts')
    def test_exception(self, mock_discover):
        mock_discover.side_effect = Exception("unexpected error")
        assert auto_discover_host() is None
