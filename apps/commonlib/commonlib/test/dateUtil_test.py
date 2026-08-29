import pytest
from unittest.mock import patch, MagicMock
from zoneinfo import ZoneInfo
from commonlib.dateUtil import getDatetimeNow, getTimeUnits, getSeconds, getDatetimeNowStr, parseDatetime, get_tz


class TestTimeFunctions:
    @patch("commonlib.dateUtil.datetime")
    def test_get_datetime_now(self, mock_datetime):
        mock_now = MagicMock()
        mock_now.timestamp.return_value = 1234567890
        mock_datetime.now.return_value = mock_now
        result = getDatetimeNow()
        assert result == 1234567890

    @patch("commonlib.dateUtil.datetime")
    def test_get_datetime_now_with_tz(self, mock_datetime):
        mock_now = MagicMock()
        mock_now.timestamp.return_value = 1234567890
        mock_datetime.now.return_value = mock_now
        with patch("commonlib.dateUtil.get_tz", return_value=MagicMock()):
            result = getDatetimeNow()
            assert result == 1234567890

    @pytest.mark.parametrize("seconds,expected", [(65, "1m 5s"), (3665, "1h 1m 5s"), (0, "0s")])
    def test_get_time_units(self, seconds, expected):
        result = getTimeUnits(seconds)
        assert result == expected

    @pytest.mark.parametrize("seconds,expected", [(7200, "2h"), (3600, "1h")])
    def test_get_time_units_hours_only(self, seconds, expected):
        result = getTimeUnits(seconds)
        assert result == expected

    @pytest.mark.parametrize("time_str,expected_seconds", [
        ("30s", 30), ("2m", 120), ("1h", 3600),
        ("1h 30m", 5400), ("1h 1m 1s", 3661), ("   1h   30m   ", 5400),
    ])
    def test_get_seconds(self, time_str, expected_seconds):
        assert getSeconds(time_str) == expected_seconds

    def test_get_seconds_invalid_unit(self):
        with pytest.raises(ValueError, match="Invalid time string"):
            getSeconds("5x")

    def test_get_seconds_empty_parts(self):
        result = getSeconds("1h  30m")
        assert result == 5400


class TestGetTz:
    @patch.dict("os.environ", {"GLOBAL_TZ": "Europe/Madrid"})
    def test_get_tz_valid(self):
        tz = get_tz()
        assert tz is not None
        assert str(tz) == "Europe/Madrid"

    @patch.dict("os.environ", {"GLOBAL_TZ": ""})
    def test_get_tz_empty(self):
        tz = get_tz()
        assert tz is None

    @patch.dict("os.environ", {"GLOBAL_TZ": "Invalid/Zone"})
    def test_get_tz_invalid(self):
        tz = get_tz()
        assert tz is None

    @patch.dict("os.environ", {}, clear=False)
    def test_get_tz_not_set(self):
        import os
        os.environ.pop("GLOBAL_TZ", None)
        tz = get_tz()
        assert tz is None


class TestDatetimeStr:
    @patch("commonlib.dateUtil.datetime")
    def test_get_datetime_now_str(self, mock_datetime):
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2024-01-15 10:30:00"
        mock_datetime.now.return_value = mock_now
        result = getDatetimeNowStr()
        assert result == "2024-01-15 10:30:00"

    @patch("commonlib.dateUtil.datetime")
    def test_get_datetime_now_str_with_tz(self, mock_datetime):
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2024-01-15 10:30:00"
        mock_datetime.now.return_value = mock_now
        with patch("commonlib.dateUtil.get_tz", return_value=MagicMock()):
            result = getDatetimeNowStr()
            assert result == "2024-01-15 10:30:00"


class TestParseDatetime:
    def test_parse_datetime_without_tz(self):
        result = parseDatetime("2024-01-15 10:30:00")
        assert isinstance(result, float)
        assert result > 0

    @patch("commonlib.dateUtil.get_tz", return_value=ZoneInfo("UTC"))
    def test_parse_datetime_with_tz(self, mock_tz):
        result = parseDatetime("2024-01-15 10:30:00")
        assert isinstance(result, float)

    def test_parse_datetime_invalid_format(self):
        with pytest.raises(ValueError):
            parseDatetime("not-a-date")
