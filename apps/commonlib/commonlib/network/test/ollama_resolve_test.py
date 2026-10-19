from unittest.mock import patch, MagicMock
import pytest
from commonlib.network.ollama_discovery import get_local_ip
from commonlib.network.ollama_resolve import auto_discover_host, resolve_ollama_host


class TestAutoDiscoverHost:
    @patch('commonlib.network.ollama_resolve.discover_ollama_hosts')
    @patch('commonlib.network.ollama_resolve.verify_ollama')
    def test_found(self, mock_verify, mock_discover):
        mock_discover.return_value = ['192.168.1.10', '192.168.1.20']
        mock_verify.side_effect = [False, True]
        assert auto_discover_host() == '192.168.1.20'

    @patch('commonlib.network.ollama_resolve.discover_ollama_hosts')
    def test_no_candidates(self, mock_discover):
        mock_discover.return_value = []
        assert auto_discover_host() is None

    @patch('commonlib.network.ollama_resolve.discover_ollama_hosts')
    @patch('commonlib.network.ollama_resolve.verify_ollama')
    def test_no_verified(self, mock_verify, mock_discover):
        mock_discover.return_value = ['192.168.1.10']
        mock_verify.return_value = False
        assert auto_discover_host() is None

    @patch('commonlib.network.ollama_resolve.discover_ollama_hosts')
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

    @patch('commonlib.network.ollama_resolve.discover_ollama_hosts')
    @patch('commonlib.network.ollama_resolve.get_local_ip')
    @patch('commonlib.network.ollama_resolve.verify_ollama')
    def test_auto_skips_local(self, mock_verify, mock_local, mock_discover):
        mock_local.return_value = '192.168.1.10'
        mock_discover.return_value = ['192.168.1.10', '192.168.1.50']
        mock_verify.return_value = True
        assert resolve_ollama_host('auto') == '192.168.1.50'
        mock_verify.assert_any_call('192.168.1.50')
        assert mock_verify.call_count == 1

    @patch('commonlib.network.ollama_resolve.discover_ollama_hosts')
    @patch('commonlib.network.ollama_resolve.get_local_ip')
    def test_auto_none_found(self, mock_local, mock_discover):
        mock_local.return_value = '192.168.1.10'
        mock_discover.return_value = ['192.168.1.50']
        with pytest.raises(ConnectionError):
            resolve_ollama_host('auto')

    @patch('commonlib.network.ollama_resolve.verify_ollama')
    def test_explicit_ip_verified(self, mock_verify):
        mock_verify.return_value = True
        assert resolve_ollama_host('192.168.1.50') == '192.168.1.50'

    @patch('commonlib.network.ollama_resolve.verify_ollama')
    def test_explicit_ip_not_verified(self, mock_verify):
        mock_verify.return_value = False
        with pytest.raises(ConnectionError):
            resolve_ollama_host('192.168.1.50')

    @patch('commonlib.network.ollama_resolve.discover_ollama_hosts')
    def test_default_is_auto(self, mock_discover):
        mock_discover.return_value = []
        with pytest.raises(ConnectionError):
            resolve_ollama_host()
