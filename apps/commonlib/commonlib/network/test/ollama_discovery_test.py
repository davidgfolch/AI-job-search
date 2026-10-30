from unittest.mock import patch, MagicMock
from commonlib.network.ollama_discovery import (
    get_local_subnets, _scan_port, _scan_hosts, discover_ollama_hosts,
)


class TestGetLocalSubnets:
    def test_returns_subnets(self):
        subnets = get_local_subnets()
        assert isinstance(subnets, list)
        if subnets:
            assert all('/' in s for s in subnets)

    @patch('commonlib.network.discovery.socket.socket')
    def test_returns_empty_on_failure(self, mock_socket_class):
        inst = MagicMock()
        inst.connect.side_effect = Exception("no network")
        mock_socket_class.return_value = inst
        # Detection fails, but common LAN defaults are still returned.
        assert get_local_subnets() == ['192.168.1.0/24', '192.168.0.0/24']

    @patch('commonlib.network.ollama_discovery.OLLAMA_DISCOVERY_SUBNETS', ('192.168.7.0/24', '10.0.0.0/24'))
    def test_includes_configured_subnets(self):
        subnets = get_local_subnets()
        assert '192.168.7.0/24' in subnets
        assert '10.0.0.0/24' in subnets

    @patch('commonlib.network.ollama_discovery.OLLAMA_DISCOVERY_SUBNETS', ('192.168.7.0/24',))
    def test_configured_subnets_deduped(self):
        subnets = get_local_subnets()
        assert subnets.count('192.168.7.0/24') == 1

    def test_default_includes_common_lan_subnets(self):
        subnets = get_local_subnets()
        assert '192.168.1.0/24' in subnets
        assert '192.168.0.0/24' in subnets


class TestScanPort:
    @patch('commonlib.network.discovery.socket.socket')
    def test_port_open(self, mock_socket):
        inst = MagicMock()
        inst.connect_ex.return_value = 0
        mock_socket.return_value = inst
        assert _scan_port('192.168.1.1', 11434, 0.5) is True

    @patch('commonlib.network.discovery.socket.socket')
    def test_port_closed(self, mock_socket):
        inst = MagicMock()
        inst.connect_ex.return_value = 1
        mock_socket.return_value = inst
        assert _scan_port('192.168.1.1', 11434, 0.5) is False

    @patch('commonlib.network.discovery.socket.socket')
    def test_exception(self, mock_socket_class):
        inst = MagicMock()
        inst.connect_ex.side_effect = OSError("connection error")
        mock_socket_class.return_value = inst
        assert _scan_port('192.168.1.1', 11434, 0.5) is False


class TestScanHosts:
    @patch('commonlib.network.ollama_discovery._scan_port')
    def test_returns_responsive_ips(self, mock_scan_port):
        def scan_side_effect(host, port, timeout):
            return host.endswith('.10')
        mock_scan_port.side_effect = scan_side_effect
        result = _scan_hosts(['192.168.1.10', '192.168.1.20'], 11434, 0.5)
        assert result == ['192.168.1.10']


class TestDiscoverOllamaHosts:
    @patch('commonlib.network.ollama_discovery._scan_hosts')
    def test_with_targets(self, mock_scan):
        mock_scan.return_value = ['192.168.1.10', '192.168.1.20']
        result = discover_ollama_hosts(targets=['192.168.1.10', '192.168.1.20'])
        assert result == ['192.168.1.10', '192.168.1.20']
        mock_scan.assert_called_once_with(['192.168.1.10', '192.168.1.20'], 11434, 0.5)

    @patch('commonlib.network.ollama_discovery._scan_hosts')
    def test_with_subnets(self, mock_scan):
        mock_scan.return_value = ['192.168.1.5']
        result = discover_ollama_hosts(subnets=['10.0.0.0/24'])
        assert result == ['192.168.1.5']

    @patch('commonlib.network.ollama_discovery.get_local_subnets')
    @patch('commonlib.network.ollama_discovery._scan_hosts')
    def test_auto_subnets(self, mock_scan, mock_subnets):
        mock_subnets.return_value = ['192.168.1.0/24']
        mock_scan.return_value = ['192.168.1.5']
        result = discover_ollama_hosts()
        mock_subnets.assert_called_once()
        assert result == ['192.168.1.5']

    @patch('commonlib.network.ollama_discovery._scan_hosts')
    def test_no_targets_no_subnets(self, mock_scan):
        mock_scan.return_value = []
        with patch('commonlib.network.ollama_discovery.get_local_subnets', return_value=[]):
            result = discover_ollama_hosts()
        assert result == []

    @patch('commonlib.network.ollama_discovery._scan_hosts')
    def test_invalid_subnet_skipped(self, mock_scan):
        mock_scan.return_value = []
        result = discover_ollama_hosts(subnets=['not-a-cidr', '192.168.1.0/24'])
        assert result == []
