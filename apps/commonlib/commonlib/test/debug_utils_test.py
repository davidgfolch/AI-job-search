from unittest.mock import patch

from commonlib import debug_utils
from commonlib.debug_utils import debug
from commonlib.terminalColor import stripAnsi


def test_debug_disabled_logs_error_without_pausing():
    with patch.object(debug_utils, 'logger') as mock_logger, patch.object(debug_utils, 'input', create=True) as mock_input:
        debug(False, 'something went wrong')

    mock_logger.error.assert_called_once()
    assert mock_logger.error.call_args[0][0] == 'debug.message'
    mock_input.assert_not_called()


def test_debug_disabled_with_exception_logs_the_exception():
    with patch.object(debug_utils, 'logger') as mock_logger, patch.object(debug_utils, 'input', create=True) as mock_input:
        debug(False, 'boom', True)

    mock_logger.exception.assert_called_once()
    assert mock_logger.exception.call_args[0][0] == 'debug.interrupted'
    mock_input.assert_not_called()


def test_debug_enabled_pauses_for_a_key():
    with patch.object(debug_utils, 'logger'), patch.object(debug_utils, 'input', create=True) as mock_input:
        debug(True, 'press a key', False)

    mock_input.assert_called_once()
    printed = stripAnsi(mock_input.call_args[0][0])
    assert 'press a key' in printed
    assert 'debug active' in printed


def test_debug_enabled_with_exception_prints_the_traceback():
    try:
        raise ValueError('boom')
    except ValueError:
        with patch.object(debug_utils, 'logger'), patch.object(debug_utils, 'input', create=True) as mock_input:
            debug(True, 'context', True)

    assert 'ValueError' in stripAnsi(mock_input.call_args[0][0])


def test_debug_enabled_without_active_exception_reports_no_traceback():
    with patch.object(debug_utils, 'logger'), patch.object(debug_utils, 'input', create=True) as mock_input:
        debug(True, 'context', True)

    assert 'No traceback available.' in stripAnsi(mock_input.call_args[0][0])
