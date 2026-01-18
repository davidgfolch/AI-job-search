import pytest
from scrapper.selectors import tecnoempleoSelectors

class TestTecnoempleoSelectors:
    def test_constants_defined(self):
        assert hasattr(tecnoempleoSelectors, 'CSS_SEL_JOB_LI')
        assert isinstance(tecnoempleoSelectors.CSS_SEL_JOB_LI, str)
        assert hasattr(tecnoempleoSelectors, 'CSS_SEL_NEXT_PAGE_BUTTON')
        assert isinstance(tecnoempleoSelectors.CSS_SEL_NEXT_PAGE_BUTTON, str)
