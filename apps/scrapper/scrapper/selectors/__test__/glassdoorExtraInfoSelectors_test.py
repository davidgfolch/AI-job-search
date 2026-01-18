import pytest
from scrapper.selectors import glassdoorExtraInfoSelectors

class TestGlassdoorExtraInfoSelectors:
    def test_constants_defined(self):
        assert hasattr(glassdoorExtraInfoSelectors, 'CSS_SEL_COMPANIES')
        assert isinstance(glassdoorExtraInfoSelectors.CSS_SEL_COMPANIES, str)
        assert hasattr(glassdoorExtraInfoSelectors, 'CSS_SEL_COMPANY_SEARCH')
        assert isinstance(glassdoorExtraInfoSelectors.CSS_SEL_COMPANY_SEARCH, str)
