import pytest
from unittest.mock import MagicMock, patch
from scrapper.core.scrapper_config import TIMER
from scrapper.core.scrapper_state_calculator import ScrapperStateCalculator

@pytest.fixture
def mocks():
    pm = MagicMock()
    pm.get_last_execution.return_value = None
    pm.get_failed_keywords.return_value = []
    pm.get_state.return_value = {}
    return {'pm': pm}

class TestScrapperStateCalculator:

    @pytest.mark.parametrize("starting, startingAt, name, timer, lapsed, expected_state", [
        (False, None, 'Infojobs', 7200, 8000, (0, "Ready", "NOW", "Default", "2h")), # Expired
        (False, None, 'Linkedin', 3600, 1000, (2600, "Pending", "43m 20s", "Default", "1h")), # Not expired
        (True, 'Infojobs', 'Infojobs', 7200, 1000, (0, "STARTING TARGET", "NOW", "Default", "2h")), # Starting target
        (True, 'Infojobs', 'Linkedin', 3600, 5000, (999999999, "Skipped (Start)", "-", "Default", "1h")), # Starting other
    ])
    def test_calculate(self, mocks, starting, startingAt, name, timer, lapsed, expected_state):
        with patch('scrapper.core.scrapper_state_calculator.getDatetimeNow', return_value=10000):
            with patch('scrapper.core.scrapper_state_calculator.parseDatetime', return_value=10000-lapsed):
                 mocks['pm'].get_last_execution.return_value = "some_date"
                 props = {TIMER: timer}
                 calculator = ScrapperStateCalculator(name, props, mocks['pm'])
                 result = calculator.calculate(starting, startingAt)
                 assert result == expected_state

    @pytest.mark.parametrize("error_lapsed, expected_state", [
        (1000, (1800-1000, "Error Wait", "13m 20s", "Error Wait", "30m")), # Error wait active
        (2000, (2600, "Pending", "43m 20s", "Default", "1h")), # Error expired (wait normal timer, assuming 3600 timer and 1000 lapsed for exec)
    ])
    def test_calculate_error(self, mocks, error_lapsed, expected_state):
        name = 'Linkedin'
        timer = 3600
        exec_lapsed = 1000
        now = 10000
        
        with patch('scrapper.core.scrapper_state_calculator.getDatetimeNow', return_value=now):
            with patch('scrapper.core.scrapper_state_calculator.parseDatetime') as mock_parse:
                def side_effect_parse(date_str):
                    if date_str == "last_exec": return now - exec_lapsed
                    if date_str == "last_error": return now - error_lapsed
                    return 0
                mock_parse.side_effect = side_effect_parse
                
                mocks['pm'].get_last_execution.return_value = "last_exec"
                
                def get_state_side_effect(n):
                    if n == name:
                        return {"last_error_time": "last_error"}
                    return {}
                mocks['pm'].get_state.side_effect = get_state_side_effect
                
                props = {TIMER: timer}
                calculator = ScrapperStateCalculator(name, props, mocks['pm'])
                result = calculator.calculate(False, None)
                assert result == expected_state

    def test_resolve_timer_default(self, mocks):
        props = {}
        calculator = ScrapperStateCalculator("Test", props, mocks['pm'])
        # Mock getEnvByPrefix to return empty
        with patch('scrapper.core.scrapper_state_calculator.getEnvByPrefix', return_value={}):
             # Mock getDatetimeNow
             with patch('scrapper.core.scrapper_state_calculator.getDatetimeNow', return_value=10000):
                 val, source = calculator.resolve_timer(3600)
                 assert val == 3600
                 assert source == "Default"
