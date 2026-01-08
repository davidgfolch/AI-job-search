
import pytest
from unittest.mock import patch, MagicMock
from scrapper.core.scrapper_scheduler import ScrapperScheduler
from commonlib.dateUtil import getSeconds
from datetime import datetime

class TestCadencyResolution:

    @pytest.fixture
    def scheduler(self):
        return ScrapperScheduler(MagicMock(), MagicMock())
    
    def get_timestamp_for_hour(self, hour):
        dt = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
        return dt.timestamp()

    @pytest.mark.parametrize("current_hour, env_vars, default_timer, expected_timer, expected_range", [
        (10, {}, 3600, 3600, "Default"),
        (10, {'7-18': '1h'}, 7200, 3600, "7-18"),
        (20, {'7-18': '1h'}, 7200, 7200, "Default"),
        (10, {'7-18': '1h', '19-22': '30m'}, 7200, 3600, "7-18"),
    ])
    def test_resolve_timer(self, scheduler, current_hour, env_vars, default_timer, expected_timer, expected_range):
         # We now patch getEnvByPrefix to return the dictionary directly
         # The env_vars in parametrize are simplified to be what getEnvByPrefix would return
         # i.e., keys are suffixes, not full env vars
        with patch('scrapper.core.scrapper_scheduler.getEnvByPrefix', return_value=env_vars):
            ts = self.get_timestamp_for_hour(current_hour)
            with patch('scrapper.core.scrapper_scheduler.getDatetimeNow', return_value=ts):
                actual_timer, actual_range = scheduler.resolve_timer('Infojobs', default_timer)
                assert actual_timer == expected_timer
                assert actual_range == expected_range

    @pytest.mark.parametrize("env_vars", [
        ({'22-6': '1h'}),  # Overnight not supported
        ({'INVALID': '1h'}), # Invalid format
    ])
    def test_resolve_timer_error(self, scheduler, env_vars):
        with patch('scrapper.core.scrapper_scheduler.getEnvByPrefix', return_value=env_vars):
            with patch('scrapper.core.scrapper_scheduler.getDatetimeNow', return_value=100000): # Any time
                with pytest.raises(ValueError):
                    scheduler.resolve_timer('Infojobs', 3600)
