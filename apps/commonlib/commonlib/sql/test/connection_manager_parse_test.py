"""Tests for IP range and host target parsing in connection_manager."""
import pytest
from commonlib.sql import connection_manager


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
