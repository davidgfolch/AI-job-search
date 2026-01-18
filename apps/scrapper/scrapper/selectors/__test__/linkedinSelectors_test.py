import pytest
from scrapper.selectors import linkedinSelectors

class TestLinkedinSelectors:
    def test_constants_defined(self):
        assert hasattr(linkedinSelectors, 'CSS_SEL_JOB_LI')
        assert isinstance(linkedinSelectors.CSS_SEL_JOB_LI, str)
        assert hasattr(linkedinSelectors, 'CSS_SEL_NEXT_PAGE_BUTTON')
        assert isinstance(linkedinSelectors.CSS_SEL_NEXT_PAGE_BUTTON, str)
