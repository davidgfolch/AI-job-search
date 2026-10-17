from unittest.mock import patch, MagicMock
import pytest
from commonlib.network.ollama_discovery import (
    get_local_subnets, get_local_ip, _scan_port, _scan_hosts, discover_ollama_hosts,
    verify_ollama, auto_discover_host, resolve_ollama_host,
)


class TestGetLocalSubnets:
    def test_returns_subnets(self):
        subnets = get_local_subnets()
        assert isinstance(subnets, list)
        if subnets:
            assert all('/' in s for s in subnets)

    @patch('commonlib.network.ollama_discovery.socket.socket')
    def test_returns_empty_on_failure(self, mock_socket_class):
        inst = MagicMock()
        inst.connect.side_effect = Exception("no network")
        mock_socket_class.return_value = inst
        assert get_local_subnets() == []


class TestScanPort:
    @patch('commonlib.network.ollama_discovery.socket.socket')
    def test_port_open(self, mock_socket):
        inst = MagicMock()
        inst.connect_ex.return_value = 0
        mock_socket.return_value = inst
        assert _scan_port('192.168.1.1', 11434, 0.5) is True

    @patch('commonlib.network.ollama_discovery.socket.socket')
    def test_port_closed(self, mock_socket):
        inst = MagicMock()
        inst.connect_ex.return_value = 1
        mock_socket.return_value = inst
        assert _scan_port('192.168.1.1', 11434, 0.5) is False

    @patch('commonlib.network.ollama_discovery.socket.socket')
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


class TestVerifyOllama:
    @patch('commonlib.network.ollama_discovery.requests.get')
    def test_verified(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        mock_get.return_value = resp
        assert verify_ollama('192.168.1.10') is True
        mock_get.assert_called_once_with('http://192.168.1.10:11434/api/tags', timeout=3)

    @patch('commonlib.network.ollama_discovery.requests.get')
    def test_http_error(self, mock_get):
        resp = MagicMock()
        resp.raise_for_status.side_effect = Exception("404")
        mock_get.return_value = resp
        assert verify_ollama('192.168.1.10') is False

    @patch('commonlib.network.ollama_discovery.requests.get')
    def test_non_2xx_status(self, mock_get):
        resp = MagicMock()
        resp.status_code = 500
        mock_get.return_value = resp
        assert verify_ollama('192.168.1.10') is False

    @patch('commonlib.network.ollama_discovery.urllib.request.urlopen')
    @patch('commonlib.network.ollama_discovery.requests.get')
    def test_connection_failure(self, mock_get, mock_urlopen):
        mock_get.side_effect = Exception("connection refused")
        mock_urlopen.side_effect = Exception("connection refused")
        assert verify_ollama('192.168.1.10') is False

    @patch('commonlib.network.ollama_discovery.urllib.request.urlopen')
    def test_urllib_fallback(self, mock_urlopen):
        resp = MagicMock()
        resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = resp
        with patch('commonlib.network.ollama_discovery.requests', None):
            assert verify_ollama('192.168.1.10') is True

    @patch('commonlib.network.ollama_discovery.urllib.request.urlopen')
    def test_urllib_fallback_failure(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("no route")
        with patch('commonlib.network.ollama_discovery.requests', None):
            assert verify_ollama('192.168.1.10') is False


class TestAutoDiscoverHost:
    @patch('commonlib.network.ollama_discovery.discover_ollama_hosts')
    @patch('commonlib.network.ollama_discovery.verify_ollama')
    def test_found(self, mock_verify, mock_discover):
        mock_discover.return_value = ['192.168.1.10', '192.168.1.20']
        mock_verify.side_effect = [False, True]
        assert auto_discover_host() == '192.168.1.20'

    @patch('commonlib.network.ollama_discovery.discover_ollama_hosts')
    def test_no_candidates(self, mock_discover):
        mock_discover.return_value = []
        assert auto_discover_host() is None

    @patch('commonlib.network.ollama_discovery.discover_ollama_hosts')
    @patch('commonlib.network.ollama_discovery.verify_ollama')
    def test_no_verified(self, mock_verify, mock_discover):
        mock_discover.return_value = ['192.168.1.10']
        mock_verify.return_value = False
        assert auto_discover_host() is None

    @patch('commonlib.network.ollama_discovery.discover_ollama_hosts')
    def test_exception(self, mock_discover):
        mock_discover.side_effect = Exception("unexpected error")
        assert auto_discover_host() is None


class TestGetLocalIp:
    @patch('commonlib.network.ollama_discovery.socket.socket')
    def test_returns_ip(self, mock_socket_class):
        inst = MagicMock()
        inst.getsockname.return_value = ('192.168.1.10', 50000)
        mock_socket_class.return_value = inst
        assert get_local_ip() == '192.168.1.10'

    @patch('commonlib.network.ollama_discovery.socket.socket')
    def test_failure(self, mock_socket_class):
        inst = MagicMock()
        inst.connect.side_effect = Exception("no network")
        mock_socket_class.return_value = inst
        assert get_local_ip() is None


class TestResolveOllamaHost:
    @pytest.mark.parametrize("spec", ['local', 'localhost', '127.0.0.1', 'LOCAL'])
    def test_local(self, spec):
        assert resolve_ollama_host(spec) == '127.0.0.1'

    @patch('commonlib.network.ollama_discovery.discover_ollama_hosts')
    @patch('commonlib.network.ollama_discovery.get_local_ip')
    @patch('commonlib.network.ollama_discovery.verify_ollama')
    def test_auto_skips_local(self, mock_verify, mock_local, mock_discover):
        mock_local.return_value = '192.168.1.10'
        mock_discover.return_value = ['192.168.1.10', '192.168.1.50']
        mock_verify.return_value = True
        assert resolve_ollama_host('auto') == '192.168.1.50'
        mock_verify.assert_any_call('192.168.1.50')
        assert mock_verify.call_count == 1

    @patch('commonlib.network.ollama_discovery.discover_ollama_hosts')
    @patch('commonlib.network.ollama_discovery.get_local_ip')
    def test_auto_none_found(self, mock_local, mock_discover):
        mock_local.return_value = '192.168.1.10'
        mock_discover.return_value = ['192.168.1.50']
        with pytest.raises(ConnectionError):
            resolve_ollama_host('auto')

    @patch('commonlib.network.ollama_discovery.verify_ollama')
    def test_explicit_ip_verified(self, mock_verify):
        mock_verify.return_value = True
        assert resolve_ollama_host('192.168.1.50') == '192.168.1.50'

    @patch('commonlib.network.ollama_discovery.verify_ollama')
    def test_explicit_ip_not_verified(self, mock_verify):
        mock_verify.return_value = False
        with pytest.raises(ConnectionError):
            resolve_ollama_host('192.168.1.50')

    @patch('commonlib.network.ollama_discovery.discover_ollama_hosts')
    def test_default_is_auto(self, mock_discover):
        mock_discover.return_value = []
        with pytest.raises(ConnectionError):
            resolve_ollama_host()
