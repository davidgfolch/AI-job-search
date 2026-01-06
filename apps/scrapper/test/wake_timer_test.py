
import pytest
from unittest.mock import MagicMock, patch, call
from commonlib.terminalUtil import consoleTimer, Spinner
from commonlib.wake_timer import WakeableTimer

import sys

@pytest.fixture
def mock_sleep():
    with patch('commonlib.wake_timer.time.sleep') as mock:
        yield mock

@pytest.fixture
def mock_windows_api():
    with patch('ctypes.windll.kernel32') as mock:
        yield mock

@pytest.mark.skipif(sys.platform != 'win32', reason="Windows only")
@patch('platform.system')
def test_wakeable_timer_windows(mock_platform, mock_windows_api):
    mock_platform.return_value = 'Windows'
    # Mock CreateWaitableTimerW to return a handle
    mock_windows_api.CreateWaitableTimerW.return_value = 123
    # Mock SetWaitableTimer to return True (success)
    mock_windows_api.SetWaitableTimer.return_value = 1
    # Mock WaitForSingleObject to return 0 (WAIT_OBJECT_0)
    mock_windows_api.WaitForSingleObject.return_value = 0

    timer = WakeableTimer()
    timer.wait(1.5)

    assert mock_windows_api.CreateWaitableTimerW.called
    assert mock_windows_api.SetWaitableTimer.called
    assert mock_windows_api.WaitForSingleObject.called
    assert mock_windows_api.CloseHandle.called

@patch('platform.system')
def test_wakeable_timer_other_os(mock_platform, mock_sleep):
    mock_platform.return_value = 'Linux'
    
    timer = WakeableTimer()
    timer.wait(1.5)
    
    mock_sleep.assert_called_with(1.5)

@patch('commonlib.terminalUtil.WakeableTimer')
def test_console_timer_calls_wakeable_timer(mock_wakeable_timer_cls):
    mock_timer_instance = MagicMock()
    mock_wakeable_timer_cls.return_value = mock_timer_instance
    
    # Run for 2 ticks (e.g. 1/3 second if tickXSec is 6)
    # consoleTimer(message, timeUnit)
    # let's mock getSeconds to allow short test
    with patch('commonlib.terminalUtil.getSeconds', return_value=1):
        consoleTimer("Test message", "1s")
    
    # Expect calls to wait. 
    # Logic: 1 second * 6 ticks = 6 iterations.
    assert mock_wakeable_timer_cls.call_count >= 1
    assert mock_timer_instance.wait.called
    args, _ = mock_timer_instance.wait.call_args
    assert args[0] > 0

