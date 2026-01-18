import pytest
from scrapper.selectors import glassdoorExtraInfoSelectors

class TestGlassdoorExtraInfoSelectors:
    def test_constants_defined(self):
        assert hasattr(glassdoorExtraInfoSelectors, 'CSS_SEL_SHOW_MORE')
        assert isinstance(glassdoorExtraInfoSelectors.CSS_SEL_SHOW_MORE, str)
