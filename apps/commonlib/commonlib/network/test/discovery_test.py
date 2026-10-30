"""Tests for the shared LAN scanner primitives used by MySQL / Mongo / Ollama discovery."""
from unittest.mock import MagicMock, patch

import pytest

from commonlib.network import discovery


class TestGetLocalIp:
    @patch('commonlib.network.discovery.socket.socket')
    def test_returns_ip(self, mock_socket_class):
        inst = MagicMock()
        inst.getsockname.return_value = ('192.168.1.10', 50000)
        mock_socket_class.return_value = inst
        assert discovery.get_local_ip() == '192.168.1.10'

    @patch('commonlib.network.discovery.socket.socket')
    def test_failure(self, mock_socket_class):
        inst = MagicMock()
        inst.connect.side_effect = Exception("no network")
        mock_socket_class.return_value = inst
        assert discovery.get_local_ip() is None


class TestConfiguredSubnets:
    @pytest.mark.parametrize("raw, expected", [
        ("", ()),
        (" 192.168.7.0/24 , 10.0.0.0/24 ,", ('192.168.7.0/24', '10.0.0.0/24')),
    ], ids=["empty", "comma-separated"])
    def test_parses_env(self, monkeypatch, raw, expected):
        monkeypatch.setenv(discovery.SUBNETS_ENV, raw)
        assert discovery.configured_subnets() == expected


class TestGetLocalSubnets:
    @patch('commonlib.network.discovery.get_local_ip', return_value='192.168.5.42')
    def test_detected_subnet_plus_neighbours_and_defaults(self, _local_ip):
        subnets = discovery.get_local_subnets()
        assert subnets[:3] == ['192.168.5.0/24', '192.168.4.0/24', '192.168.6.0/24']
        assert '192.168.1.0/24' in subnets
        assert '192.168.0.0/24' in subnets

    @patch('commonlib.network.discovery.get_local_ip', return_value=None)
    def test_detection_failure_still_returns_common_lans(self, _local_ip):
        assert discovery.get_local_subnets() == ['192.168.1.0/24', '192.168.0.0/24']

    @patch('commonlib.network.discovery.get_local_ip', return_value='192.168.1.10')
    def test_common_lan_not_duplicated(self, _local_ip):
        subnets = discovery.get_local_subnets()
        assert subnets.count('192.168.1.0/24') == 1

    @patch('commonlib.network.discovery.get_local_ip', return_value='192.168.1.10')
    def test_configured_and_extra_subnets_appended_once(self, _local_ip, monkeypatch):
        monkeypatch.setenv(discovery.SUBNETS_ENV, '192.168.7.0/24')
        subnets = discovery.get_local_subnets(extra_subnets=('192.168.7.0/24', '10.0.0.0/24'))
        assert subnets.count('192.168.7.0/24') == 1
        assert subnets[-1] == '10.0.0.0/24'

    @patch('commonlib.network.discovery.get_local_ip', return_value='10.0.0.1')
    def test_lower_bound_subnet_skipped(self, _local_ip):
        subnets = discovery.get_local_subnets()
        assert subnets[:2] == ['10.0.0.0/24', '10.0.1.0/24']
        assert all('/' in subnet for subnet in subnets)

    @patch('commonlib.network.discovery.get_local_ip', return_value='10.0.255.1')
    def test_upper_bound_subnet_skipped(self, _local_ip):
        subnets = discovery.get_local_subnets()
        assert subnets[:2] == ['10.0.255.0/24', '10.0.254.0/24']
        assert '10.0.256.0/24' not in subnets


class TestScanPort:
    @pytest.mark.parametrize("result, expected", [(0, True), (1, False)], ids=["open", "closed"])
    @patch('commonlib.network.discovery.socket.socket')
    def test_connect_result(self, mock_socket, result, expected):
        inst = MagicMock()
        inst.connect_ex.return_value = result
        mock_socket.return_value = inst
        assert discovery.scan_port('192.168.1.1', 3306, 0.5) is expected

    @patch('commonlib.network.discovery.socket.socket')
    def test_exception_is_closed(self, mock_socket_class):
        inst = MagicMock()
        inst.connect_ex.side_effect = OSError("connection error")
        mock_socket_class.return_value = inst
        assert discovery.scan_port('192.168.1.1', 3306, 0.5) is False
        inst.close.assert_called_once()


class TestSubnetHosts:
    @pytest.mark.parametrize("subnets, expected", [
        (['192.168.1.0/30'], ['192.168.1.1', '192.168.1.2']),
        (['not-a-cidr'], []),
        (['not-a-cidr', '10.0.0.0/30'], ['10.0.0.1', '10.0.0.2']),
    ], ids=["hosts-exclude-network-and-broadcast", "invalid-skipped", "invalid-then-valid"])
    def test_expands_subnets(self, subnets, expected):
        assert discovery.subnet_hosts(subnets) == expected

    def test_budget_caps_the_scan(self, monkeypatch):
        monkeypatch.setattr(discovery, 'MAX_SCAN_HOSTS', 3)
        hosts = discovery.subnet_hosts(['10.0.0.0/29', '10.0.1.0/29'], kind='ollama')
        assert len(hosts) == 3

    def test_no_budget_returns_every_host(self, monkeypatch):
        monkeypatch.setattr(discovery, 'MAX_SCAN_HOSTS', 0)
        assert len(discovery.subnet_hosts(['10.0.0.0/29'])) == 6
