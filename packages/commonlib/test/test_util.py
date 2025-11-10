import pytest
from unittest.mock import patch, MagicMock
import os
import time

from commonlib.util import (
    getEnv, getEnvBool, getEnvInt, getEnvFloat, 
    consoleTimer, getDatetimeNow, getTimeUnits,
    formatNumber, formatBytes, formatPercentage,
    isValidUrl, isValidEmail, cleanText,
    parseDate, formatDate, getCurrentTimestamp,
    safeInt, safeFloat, safeBool
)


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

    def test_get_env_int_valid(self):
        with patch.dict(os.environ, {'TEST_INT': '42'}):
            result = getEnvInt('TEST_INT')
            assert result == 42

    def test_get_env_int_invalid_with_default(self):
        with patch.dict(os.environ, {'TEST_INT': 'not_a_number'}):
            result = getEnvInt('TEST_INT', 10)
            assert result == 10

    def test_get_env_int_non_existing_with_default(self):
        result = getEnvInt('NON_EXISTING_INT', 5)
        assert result == 5

    def test_get_env_float_valid(self):
        with patch.dict(os.environ, {'TEST_FLOAT': '3.14'}):
            result = getEnvFloat('TEST_FLOAT')
            assert result == 3.14

    def test_get_env_float_invalid_with_default(self):
        with patch.dict(os.environ, {'TEST_FLOAT': 'not_a_float'}):
            result = getEnvFloat('TEST_FLOAT', 1.0)
            assert result == 1.0


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

    def test_get_current_timestamp(self):
        with patch('time.time', return_value=1234567890):
            result = getCurrentTimestamp()
            assert result == 1234567890


class TestFormattingFunctions:
    def test_format_number_integer(self):
        result = formatNumber(1234567)
        assert result == '1,234,567'

    def test_format_number_float(self):
        result = formatNumber(1234.56)
        assert result == '1,234.56'

    def test_format_number_zero(self):
        result = formatNumber(0)
        assert result == '0'

    def test_format_bytes_bytes(self):
        result = formatBytes(512)
        assert result == '512 B'

    def test_format_bytes_kilobytes(self):
        result = formatBytes(1536)
        assert result == '1.5 KB'

    def test_format_bytes_megabytes(self):
        result = formatBytes(1572864)
        assert result == '1.5 MB'

    def test_format_bytes_gigabytes(self):
        result = formatBytes(1610612736)
        assert result == '1.5 GB'

    def test_format_percentage_valid(self):
        result = formatPercentage(0.75)
        assert result == '75.0%'

    def test_format_percentage_zero(self):
        result = formatPercentage(0)
        assert result == '0.0%'

    def test_format_percentage_over_100(self):
        result = formatPercentage(1.5)
        assert result == '150.0%'


class TestValidationFunctions:
    def test_is_valid_url_valid_http(self):
        result = isValidUrl('http://example.com')
        assert result is True

    def test_is_valid_url_valid_https(self):
        result = isValidUrl('https://example.com')
        assert result is True

    def test_is_valid_url_invalid(self):
        result = isValidUrl('not_a_url')
        assert result is False

    def test_is_valid_url_empty(self):
        result = isValidUrl('')
        assert result is False

    def test_is_valid_url_none(self):
        result = isValidUrl(None)
        assert result is False

    def test_is_valid_email_valid(self):
        result = isValidEmail('test@example.com')
        assert result is True

    def test_is_valid_email_invalid(self):
        result = isValidEmail('not_an_email')
        assert result is False

    def test_is_valid_email_empty(self):
        result = isValidEmail('')
        assert result is False

    def test_is_valid_email_none(self):
        result = isValidEmail(None)
        assert result is False


class TestTextFunctions:
    def test_clean_text_basic(self):
        result = cleanText('  Hello World  ')
        assert result == 'Hello World'

    def test_clean_text_multiple_spaces(self):
        result = cleanText('Hello    World')
        assert result == 'Hello World'

    def test_clean_text_newlines(self):
        result = cleanText('Hello\nWorld\n')
        assert result == 'Hello World'

    def test_clean_text_tabs(self):
        result = cleanText('Hello\tWorld')
        assert result == 'Hello World'

    def test_clean_text_empty(self):
        result = cleanText('')
        assert result == ''

    def test_clean_text_none(self):
        result = cleanText(None)
        assert result == ''


class TestDateFunctions:
    def test_parse_date_valid_iso(self):
        result = parseDate('2023-12-25')
        assert result is not None
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 25

    def test_parse_date_valid_slash_format(self):
        result = parseDate('12/25/2023')
        assert result is not None

    def test_parse_date_invalid(self):
        result = parseDate('invalid_date')
        assert result is None

    def test_parse_date_empty(self):
        result = parseDate('')
        assert result is None

    def test_parse_date_none(self):
        result = parseDate(None)
        assert result is None

    def test_format_date_valid(self):
        from datetime import datetime
        date_obj = datetime(2023, 12, 25, 10, 30, 0)
        result = formatDate(date_obj)
        assert '2023' in result
        assert '12' in result
        assert '25' in result

    def test_format_date_none(self):
        result = formatDate(None)
        assert result == ''


class TestSafeFunctions:
    def test_safe_int_valid_string(self):
        result = safeInt('42')
        assert result == 42

    def test_safe_int_valid_int(self):
        result = safeInt(42)
        assert result == 42

    def test_safe_int_invalid_with_default(self):
        result = safeInt('not_a_number', 0)
        assert result == 0

    def test_safe_int_none_with_default(self):
        result = safeInt(None, -1)
        assert result == -1

    def test_safe_float_valid_string(self):
        result = safeFloat('3.14')
        assert result == 3.14

    def test_safe_float_valid_float(self):
        result = safeFloat(3.14)
        assert result == 3.14

    def test_safe_float_invalid_with_default(self):
        result = safeFloat('not_a_float', 0.0)
        assert result == 0.0

    def test_safe_float_none_with_default(self):
        result = safeFloat(None, -1.0)
        assert result == -1.0

    def test_safe_bool_true_string(self):
        result = safeBool('true')
        assert result is True

    def test_safe_bool_false_string(self):
        result = safeBool('false')
        assert result is False

    def test_safe_bool_boolean(self):
        result = safeBool(True)
        assert result is True

    def test_safe_bool_invalid_with_default(self):
        result = safeBool('invalid', False)
        assert result is False

    def test_safe_bool_none_with_default(self):
        result = safeBool(None, True)
        assert result is True