import pytest
from unittest.mock import patch
from scrapper.core.utils import debug

class TestDebug:
    @pytest.mark.parametrize("debug_mode, exception, input_se, print_count", [
        (False, False, None, 1),
        (False, True, None, 2),
        (True, False, [''], 0),
        (True, True, [''], 0) # Mock print separately if needed
    ])
    def test_debug(self, debug_mode, exception, input_se, print_count):
        with patch('builtins.print') as mp, patch('builtins.input', side_effect=input_se or []):
            debug(debug_mode, 'Msg', exception=exception)
            if not debug_mode: 
                assert mp.call_count >= print_count
