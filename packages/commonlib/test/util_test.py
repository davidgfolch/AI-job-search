import pytest
from unittest.mock import patch, MagicMock
import os
import time

from commonlib.util import getEnv, getEnvBool, consoleTimer, getDatetimeNow, getTimeUnits


class TestEnvironmentFunctions:
    def test_get_env_existing_var(self):
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            result = getEnv('TEST_VAR')
            assert result == 'test_value'

    def test_get_env_non_existing_var_with_default(self):
        result = getEnv('NON_EXISTING_VAR', 'default_value')
        assert result == 'default_value'

    def test_get_env_non_existing_var_no_default(self):
        result = getEnv('NON_EXISTING_VAR')
        assert result is None

    def test_get_env_bool_true_values(self):
        true_values = ['true', 'True', 'TRUE']
        for value in true_values:
            with patch.dict(os.environ, {'TEST_BOOL': value}):
                result = getEnvBool('TEST_BOOL')
                assert result is True, f"Expected True for value '{value}', got {result}"

    def test_get_env_bool_false_values(self):
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO', '']
        for value in false_values:
            with patch.dict(os.environ, {'TEST_BOOL': value}):
                result = getEnvBool('TEST_BOOL')
                assert result is False

    def test_get_env_bool_default(self):
        result = getEnvBool('NON_EXISTING_BOOL', True)
        assert result is True


class TestTimeFunctions:
    @patch('commonlib.util.sleep')
    def test_console_timer(self, mock_sleep):
        consoleTimer('Test message', '2s')
        # consoleTimer uses Spinner with tickXSec=6, so it calls sleep multiple times
        assert mock_sleep.called

    @patch('commonlib.util.sleep')
    def test_console_timer_minutes(self, mock_sleep):
        consoleTimer('Test message', '1m')
        assert mock_sleep.called

    @patch('commonlib.util.sleep')
    def test_console_timer_hours(self, mock_sleep):
        consoleTimer('Test message', '1h')
        assert mock_sleep.called

    @patch('commonlib.util.sleep')
    def test_console_timer_invalid_format(self, mock_sleep):
        with pytest.raises((KeyError, ValueError)):
            consoleTimer('Test message', 'invalid')

    @patch('commonlib.util.datetime')
    def test_get_datetime_now(self, mock_datetime):
        mock_now = MagicMock()
        mock_now.timestamp.return_value = 1234567890
        mock_datetime.now.return_value = mock_now
        result = getDatetimeNow()
        assert result == 1234567890

    def test_get_time_units_seconds(self):
        result = getTimeUnits(65)
        assert result == '1m 5s'

    def test_get_time_units_hours(self):
        result = getTimeUnits(3665)
        assert result == '1h 1m 5s'

    def test_get_time_units_zero(self):
        result = getTimeUnits(0)
        assert result == '0s'

