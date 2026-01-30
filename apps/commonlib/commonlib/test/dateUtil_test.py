from unittest.mock import patch, MagicMock
from commonlib.dateUtil import getDatetimeNow, getTimeUnits

class TestTimeFunctions:
    @patch('commonlib.dateUtil.datetime')
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

    def test_get_seconds(self):
        from commonlib.dateUtil import getSeconds
        assert getSeconds("30s") == 30
        assert getSeconds("2m") == 120
        assert getSeconds("1h") == 3600
        assert getSeconds("1h 30m") == 5400
        assert getSeconds("1h 1m 1s") == 3661
        assert getSeconds("   1h   30m   ") == 5400
