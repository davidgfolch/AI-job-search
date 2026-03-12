import pytest
from scrapper.core.scrapper_config import (
    TIMER, CLOSE_TAB, AUTORUN, SCRAPPERS, SCRAPPER_RUN_IN_TABS, DEBUG
)

class TestScrapperConfig:
    def test_constants_defined(self):
        assert TIMER == 'timer'
        assert CLOSE_TAB == 'closeTab'
        assert AUTORUN == 'autoRun'
    
    def test_scrappers_structure(self):
        assert isinstance(SCRAPPERS, dict)
        assert len(SCRAPPERS) > 0
        for name, config in SCRAPPERS.items():
            assert TIMER in config
            assert AUTORUN in config
            assert isinstance(config[TIMER], int)
            assert isinstance(config[AUTORUN], bool)
    
    @pytest.mark.parametrize("scrapper_name", [
        "Infojobs", "Tecnoempleo", "Linkedin", "Glassdoor", "Indeed"
    ])
    def test_required_scrappers_exist(self, scrapper_name):
        assert scrapper_name in SCRAPPERS
        assert SCRAPPERS[scrapper_name][TIMER] > 0
        assert isinstance(SCRAPPERS[scrapper_name][AUTORUN], bool)
        assert isinstance(SCRAPPERS[scrapper_name][DEBUG], bool)
    
    def test_linkedin_has_close_tab(self):
        assert CLOSE_TAB in SCRAPPERS['Linkedin']
        assert SCRAPPERS['Linkedin'][CLOSE_TAB] is True
    
