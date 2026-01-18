import pytest
from scrapper.selectors import infojobsSelectors

class TestInfojobsSelectors:
    def test_constants_defined(self):
        assert hasattr(infojobsSelectors, 'CSS_SEL_JOB_LI')
        assert isinstance(infojobsSelectors.CSS_SEL_JOB_LI, str)
        assert hasattr(infojobsSelectors, 'CSS_SEL_NEXT_PAGE_BUTTON')
        assert isinstance(infojobsSelectors.CSS_SEL_NEXT_PAGE_BUTTON, str)
