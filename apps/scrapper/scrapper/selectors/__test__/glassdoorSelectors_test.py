import pytest
from scrapper.selectors import glassdoorSelectors

class TestGlassdoorSelectors:
    def test_constants_defined(self):
        assert hasattr(glassdoorSelectors, 'CSS_SEL_JOB_LI')
        assert isinstance(glassdoorSelectors.CSS_SEL_JOB_LI, str)
        assert hasattr(glassdoorSelectors, 'CSS_SEL_NEXT_PAGE_BUTTON')
        assert isinstance(glassdoorSelectors.CSS_SEL_NEXT_PAGE_BUTTON, str)
