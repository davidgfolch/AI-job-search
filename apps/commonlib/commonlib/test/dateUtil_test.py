import pytest
from unittest.mock import patch, MagicMock
from commonlib.dateUtil import getDatetimeNow, getTimeUnits, getSeconds


class TestTimeFunctions:
    @patch("commonlib.dateUtil.datetime")
    def test_get_datetime_now(self, mock_datetime):
        mock_now = MagicMock()
        mock_now.timestamp.return_value = 1234567890
        mock_datetime.now.return_value = mock_now
        result = getDatetimeNow()
        assert result == 1234567890

    @pytest.mark.parametrize(
        "seconds,expected", [(65, "1m 5s"), (3665, "1h 1m 5s"), (0, "0s")]
    )
    def test_get_time_units(self, seconds, expected):
        result = getTimeUnits(seconds)
        assert result == expected

    @pytest.mark.parametrize(
        "time_str,expected_seconds",
        [
            ("30s", 30),
            ("2m", 120),
            ("1h", 3600),
            ("1h 30m", 5400),
            ("1h 1m 1s", 3661),
            ("   1h   30m   ", 5400),
        ],
    )
    def test_get_seconds(self, time_str, expected_seconds):
        assert getSeconds(time_str) == expected_seconds
