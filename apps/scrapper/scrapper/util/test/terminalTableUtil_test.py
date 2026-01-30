import pytest
from unittest.mock import MagicMock
from scrapper.util.terminalTableUtil import print_failed_info_table, _collect_failed_info

@pytest.fixture
def mock_pm():
    pm = MagicMock()
    pm.state = {}
    return pm

@pytest.mark.parametrize("state,expected_count", [
    ({}, 0),
    ({"Site1": {}}, 0),
    ({"Site1": {"failed_keywords": ["k1"]}}, 1),
    ({"Site1": {"last_error": "Error msg"}}, 1),
    ({"Site1": {"failed_keywords": ["k1"], "last_error": "Error"}}, 1),
    ({"Site1": {"failed_keywords": ["k1"]}, "Site2": {"last_error": "Err"}}, 2),
])
def test_collect_failed_info(mock_pm, state, expected_count):
    mock_pm.state = state
    data = _collect_failed_info(mock_pm)
    assert len(data) == expected_count

def test_collect_failed_info_with_multiple_keywords(mock_pm):
    mock_pm.state = {"TestSite": {"failed_keywords": ["kw1", "kw2", "kw3"]}}
    data = _collect_failed_info(mock_pm)
    assert len(data) == 1
    assert "kw1, kw2, kw3" in data[0][1]

def test_collect_failed_info_with_error_details(mock_pm):
    mock_pm.state = {
        "TestSite": {
            "last_error": "Connection timeout",
            "last_error_time": "2026-01-22 20:00:00"
        }
    }
    data = _collect_failed_info(mock_pm)
    assert len(data) == 1
    assert data[0][2] == "Connection timeout"
    assert data[0][3] == "2026-01-22 20:00:00"

def test_print_failed_info_table_no_failures(mock_pm, capsys):
    mock_pm.state = {"Site1": {}}
    print_failed_info_table(mock_pm)
    captured = capsys.readouterr()
    assert captured.out == ""
