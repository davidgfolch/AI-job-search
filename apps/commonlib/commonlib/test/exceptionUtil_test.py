import pytest
from unittest.mock import patch, MagicMock
from commonlib.exceptionUtil import try_or_warn, getProjectTraceItems, cleanUnresolvedTrace, filter_trace_by_paths

def test_getProjectTraceItems_basic():
    try:
        raise ValueError("Test error")
    except ValueError as e:
        trace = getProjectTraceItems(e)
        # Should contain current filename
        assert "exceptionUtil_test.py" in trace

@patch('traceback.extract_tb')
def test_getProjectTraceItems_filtering(mock_extract_tb):
    # Setup mock frames
    frame_site_packages = MagicMock()
    frame_site_packages.filename = '/usr/lib/python3.8/site-packages/somelib/module.py'
    frame_site_packages.lineno = 10
    
    frame_user_code = MagicMock()
    frame_user_code.filename = '/projects/app/main.py'
    frame_user_code.lineno = 20

    mock_extract_tb.return_value = [frame_site_packages, frame_user_code]
    
    # Create a dummy exception logic since we are mocking extract_tb which takes the traceback
    class DummyException:
        __traceback__ = "dummy_traceback"

    result = getProjectTraceItems(DummyException())
    
    # Assert 'site-packages' file is filtered out
    assert 'module.py' not in result
    # Assert user code is present
    assert 'main.py:20' in result

@pytest.mark.parametrize("input_str, expected", [
    ("Error\n0x12345678\n(nil)\nEnd", "Error\nEnd"),
    ("0x328543\n0x328584", ""),
    ("No symbol [0x00007FF7D38A0CE2]", ""),
    ("Valid content", "Valid content"),
    (None, "None"),
    ("A" * 310, "A" * 297 + "..."),
])
def test_cleanUnresolvedTrace(input_str, expected):
    assert cleanUnresolvedTrace(input_str) == expected


def test_filter_trace_by_paths_apps_only():
    try:
        raise ValueError("Test error")
    except ValueError:
        result = filter_trace_by_paths(["apps/"])
        assert "exceptionUtil_test.py" in result
        assert "site-packages" not in result


@patch('traceback.extract_tb')
@patch('traceback.format_list')
def test_filter_trace_by_paths_filters_out_non_matching(mock_format_list, mock_extract_tb):
    frame_site_packages = MagicMock()
    frame_site_packages.filename = '/usr/lib/python3.8/site-packages/somelib/module.py'
    frame_site_packages.lineno = 10
    
    frame_user_code = MagicMock()
    frame_user_code.filename = '/projects/apps/backend/main.py'
    frame_user_code.lineno = 20

    mock_extract_tb.return_value = [frame_site_packages, frame_user_code]
    mock_format_list.return_value = ['  File "/projects/apps/backend/main.py", line 20, in main\n']

    class DummyExcInfo:
        def __init__(self):
            pass

    with patch('sys.exc_info', return_value=(None, None, DummyExcInfo())):
        result = filter_trace_by_paths(["apps/"])

    assert "main.py" in result and "20" in result


def test_filter_trace_by_paths_no_trace():
    with patch('sys.exc_info', return_value=(None, None, None)):
        result = filter_trace_by_paths(["apps/"])
    assert result == ""


def ok_fn():
    return 42


def fail_fn():
    raise ValueError("test error")


@patch('commonlib.exceptionUtil.traceback.print_exc')
def test_try_or_warn_success(mock_print_exc, capsys):
    assert try_or_warn(ok_fn, "warning") is True
    captured = capsys.readouterr()
    assert captured.out == ""
    mock_print_exc.assert_not_called()


@patch('commonlib.exceptionUtil.traceback.print_exc')
def test_try_or_warn_failure_no_exception(mock_print_exc, capsys):
    assert try_or_warn(fail_fn, "test warning") is False
    captured = capsys.readouterr()
    assert "\033[93mtest warning\033[0m\n" in captured.out
    mock_print_exc.assert_not_called()


@patch('commonlib.exceptionUtil.traceback.print_exc')
def test_try_or_warn_failure_with_exception(mock_print_exc, capsys):
    assert try_or_warn(fail_fn, "test warning", show_exception=True) is False
    captured = capsys.readouterr()
    assert "\033[93mtest warning\033[0m\n" in captured.out
    mock_print_exc.assert_called_once()
