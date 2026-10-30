"""Tests for the MongoDB LAN scanner (mirrors the MySQL / Ollama discovery tests)."""
from unittest.mock import patch

from commonlib.network.mongo_discovery import (
    get_local_subnets, _scan_port, _scan_hosts, discover_mongo_hosts,
)


class TestGetLocalSubnets:
    def test_returns_subnets(self):
        subnets = get_local_subnets()
        assert isinstance(subnets, list)
        if subnets:
            assert all('/' in subnet for subnet in subnets)

    @patch('commonlib.network.discovery.socket.socket')
    def test_detection_failure_returns_common_lans(self, mock_socket_class):
        mock_socket_class.return_value.connect.side_effect = OSError("no network")
        assert get_local_subnets() == ['192.168.1.0/24', '192.168.0.0/24']

    @patch('commonlib.network.discovery.socket.socket')
    def test_unavailable_socket_still_returns_common_lans(self, mock_socket_class):
        mock_socket_class.side_effect = OSError("no sockets")
        assert get_local_subnets() == ['192.168.1.0/24', '192.168.0.0/24']


class TestScanPort:
    @patch('commonlib.network.discovery.socket.socket')
    def test_port_open(self, mock_socket):
        inst = mock_socket.return_value
        inst.connect_ex.return_value = 0
        assert _scan_port('192.168.1.1', 27017, 0.5) is True

    @patch('commonlib.network.discovery.socket.socket')
    def test_port_closed(self, mock_socket):
        inst = mock_socket.return_value
        inst.connect_ex.return_value = 1
        assert _scan_port('192.168.1.1', 27017, 0.5) is False

    @patch('commonlib.network.discovery.socket.socket')
    def test_exception(self, mock_socket_class):
        inst = mock_socket_class.return_value
        inst.connect_ex.side_effect = OSError("connection error")
        assert _scan_port('192.168.1.1', 27017, 0.5) is False


class TestScanHosts:
    @patch('commonlib.network.mongo_discovery._scan_port')
    def test_returns_responsive_ips(self, mock_scan_port):
        mock_scan_port.side_effect = lambda host, port, timeout: host.endswith('.10')
        assert _scan_hosts(['192.168.1.10', '192.168.1.20'], 27017, 0.5) == ['192.168.1.10']


class TestDiscoverMongoHosts:
    @patch('commonlib.network.mongo_discovery._scan_hosts')
    def test_with_targets(self, mock_scan):
        mock_scan.return_value = ['192.168.1.10', '192.168.1.20']
        result = discover_mongo_hosts(targets=['192.168.1.10', '192.168.1.20'])
        assert result == ['192.168.1.10', '192.168.1.20']
        mock_scan.assert_called_once_with(['192.168.1.10', '192.168.1.20'], 27017, 0.5)

    @patch('commonlib.network.mongo_discovery._scan_hosts')
    def test_with_subnets(self, mock_scan):
        mock_scan.return_value = ['192.168.1.5']
        assert discover_mongo_hosts(subnets=['10.0.0.0/24']) == ['192.168.1.5']

    @patch('commonlib.network.mongo_discovery.get_local_subnets')
    @patch('commonlib.network.mongo_discovery._scan_hosts')
    def test_auto_subnets(self, mock_scan, mock_subnets):
        mock_subnets.return_value = ['192.168.1.0/24']
        mock_scan.return_value = ['192.168.1.5']
        assert discover_mongo_hosts() == ['192.168.1.5']
        mock_subnets.assert_called_once()

    @patch('commonlib.network.mongo_discovery._scan_hosts')
    def test_no_targets_no_subnets(self, mock_scan):
        mock_scan.return_value = []
        with patch('commonlib.network.mongo_discovery.get_local_subnets', return_value=[]):
            assert discover_mongo_hosts() == []

    @patch('commonlib.network.mongo_discovery._scan_hosts')
    def test_invalid_subnet_skipped(self, mock_scan):
        mock_scan.return_value = []
        assert discover_mongo_hosts(subnets=['not-a-cidr', '192.168.1.0/24']) == []

    def test_custom_port_and_timeout(self):
        with patch('commonlib.network.mongo_discovery._scan_hosts', return_value=[]) as mock_scan:
            discover_mongo_hosts(targets=['10.0.0.1'], port=27018, timeout=0.1)
        mock_scan.assert_called_once_with(['10.0.0.1'], 27018, 0.1)
