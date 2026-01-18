import pytest
from scrapper.selectors import indeedSelectors

class TestIndeedSelectors:
    def test_constants_defined(self):
        assert hasattr(indeedSelectors, 'CSS_SEL_JOB_LI')
        assert isinstance(indeedSelectors.CSS_SEL_JOB_LI, str)
        assert hasattr(indeedSelectors, 'CSS_SEL_NEXT_PAGE_BUTTON')
        assert isinstance(indeedSelectors.CSS_SEL_NEXT_PAGE_BUTTON, str)
