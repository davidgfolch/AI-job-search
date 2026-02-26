import pytest
from scrapper.core.scrapper_config import (
    TIMER, CLOSE_TAB, IGNORE_AUTORUN, SCRAPPERS, SCRAPPER_RUN_IN_TABS
)

class TestScrapperConfig:
    def test_constants_defined(self):

        assert TIMER == 'timer'
        assert CLOSE_TAB == 'closeTab'
        assert IGNORE_AUTORUN == 'ignoreAutoRun'
    
    def test_scrappers_structure(self):
        assert isinstance(SCRAPPERS, dict)
        assert len(SCRAPPERS) > 0
        for name, config in SCRAPPERS.items():
            assert TIMER in config
            assert IGNORE_AUTORUN in config
            assert isinstance(config[TIMER], int)
            assert isinstance(config[IGNORE_AUTORUN], bool)
    
    @pytest.mark.parametrize("scrapper_name", [
        "Infojobs", "Tecnoempleo", "Linkedin", "Glassdoor", "Indeed"
    ])
    def test_required_scrappers_exist(self, scrapper_name):
        assert scrapper_name in SCRAPPERS
    
    def test_linkedin_has_close_tab(self):
        assert CLOSE_TAB in SCRAPPERS['Linkedin']
        assert SCRAPPERS['Linkedin'][CLOSE_TAB] is True
    
