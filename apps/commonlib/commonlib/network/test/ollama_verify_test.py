from unittest.mock import patch, MagicMock
import pytest
from commonlib.network.ollama_verify import verify_ollama


class TestVerifyOllama:
    @patch('commonlib.network.ollama_verify.requests.get')
    def test_verified(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        mock_get.return_value = resp
        assert verify_ollama('192.168.1.10') is True
        mock_get.assert_called_once_with('http://192.168.1.10:11434/api/tags', timeout=3)

    @patch('commonlib.network.ollama_verify.requests.get')
    def test_http_error(self, mock_get):
        resp = MagicMock()
        resp.raise_for_status.side_effect = Exception("404")
        mock_get.return_value = resp
        assert verify_ollama('192.168.1.10') is False

    @patch('commonlib.network.ollama_verify.requests.get')
    def test_non_2xx_status(self, mock_get):
        resp = MagicMock()
        resp.status_code = 500
        mock_get.return_value = resp
        assert verify_ollama('192.168.1.10') is False

    @patch('commonlib.network.ollama_verify.urllib.request.urlopen')
    @patch('commonlib.network.ollama_verify.requests.get')
    def test_connection_failure(self, mock_get, mock_urlopen):
        mock_get.side_effect = Exception("connection refused")
        mock_urlopen.side_effect = Exception("connection refused")
        assert verify_ollama('192.168.1.10') is False

    @patch('commonlib.network.ollama_verify.urllib.request.urlopen')
    def test_urllib_fallback(self, mock_urlopen):
        resp = MagicMock()
        resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = resp
        with patch('commonlib.network.ollama_verify.requests', None):
            assert verify_ollama('192.168.1.10') is True

    @patch('commonlib.network.ollama_verify.urllib.request.urlopen')
    def test_urllib_fallback_failure(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("no route")
        with patch('commonlib.network.ollama_verify.requests', None):
            assert verify_ollama('192.168.1.10') is False
