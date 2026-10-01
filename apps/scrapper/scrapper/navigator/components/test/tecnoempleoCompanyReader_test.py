import pytest
from unittest.mock import MagicMock, patch
from commonlib.company_normalizer import UNSPECIFIED_COMPANY
from scrapper.navigator.components.tecnoempleoCompanyReader import TecnoempleoCompanyReader, JS_FIRST_DIRECT_TEXT_NODE
from scrapper.navigator.tecnoempleoNavigator import CSS_JOB_DETAIL_HEADER, CSS_SEL_COMPANY
from selenium.common.exceptions import NoSuchElementException

HEADER_CSS = CSS_JOB_DETAIL_HEADER

class TestTecnoempleoCompanyReader:

    @pytest.fixture
    def mock_selenium(self):
        selenium = MagicMock()
        selenium.driver.execute_script.return_value = ''  # no bare text node in the header by default
        return selenium

    @pytest.fixture
    def reader(self, mock_selenium):
        return TecnoempleoCompanyReader(mock_selenium, CSS_SEL_COMPANY, HEADER_CSS)

    def test_read_link(self, reader, mock_selenium):
        mock_selenium.getText.return_value = "  Acme  "
        assert reader.read() == "Acme"
        mock_selenium.getText.assert_called_with(CSS_SEL_COMPANY)

    def test_read_link_wins_over_text_node(self, reader, mock_selenium):
        mock_selenium.getText.return_value = "Acme"
        mock_selenium.driver.execute_script.return_value = "Wrong Company"
        assert reader.read() == "Acme"
        mock_selenium.driver.execute_script.assert_not_called()

    @pytest.mark.parametrize("text", ["", "   "])
    def test_read_blank_link(self, reader, mock_selenium, text):
        mock_selenium.getText.return_value = text
        assert reader.read() == UNSPECIFIED_COMPANY

    def test_read_link_element_not_found(self, reader, mock_selenium):
        """tecnoempleo sometimes renders no company link, the job must not be discarded"""
        mock_selenium.getText.side_effect = NoSuchElementException("no company")
        with patch('commonlib.decorator.retry.sleep'):
            assert reader.read() == UNSPECIFIED_COMPANY

    def test_read_link_other_error(self, reader, mock_selenium):
        mock_selenium.getText.side_effect = ValueError("stale page")
        assert reader.read() == UNSPECIFIED_COMPANY

    def test_read_link_retries_before_fallback(self, reader, mock_selenium):
        mock_selenium.getText.side_effect = [NoSuchElementException("not rendered yet"), "Acme"]
        with patch('commonlib.decorator.retry.sleep'):
            assert reader.read() == "Acme"

    def test_read_falls_back_to_header_text_node(self, reader, mock_selenium):
        """An offer with no company page renders its name as a bare text node in the header"""
        mock_selenium.getText.side_effect = NoSuchElementException("no company link")
        mock_selenium.driver.execute_script.return_value = " Sngular "
        headerElm = mock_selenium.getElm.return_value
        with patch('commonlib.decorator.retry.sleep'):
            assert reader.read() == "Sngular"
        mock_selenium.getElm.assert_called_once_with(HEADER_CSS)
        mock_selenium.driver.execute_script.assert_called_once_with(JS_FIRST_DIRECT_TEXT_NODE, headerElm)

    @pytest.mark.parametrize("textNode", ["", "   ", None])
    def test_read_blank_text_node(self, reader, mock_selenium, textNode):
        """appcast offers have no employer at all, they fall back to the unspecified sentinel"""
        mock_selenium.getText.side_effect = NoSuchElementException("no company link")
        mock_selenium.driver.execute_script.return_value = textNode
        with patch('commonlib.decorator.retry.sleep'):
            assert reader.read() == UNSPECIFIED_COMPANY

    def test_read_text_node_error(self, reader, mock_selenium):
        mock_selenium.getText.side_effect = NoSuchElementException("no company link")
        mock_selenium.getElm.side_effect = NoSuchElementException("no header")
        with patch('commonlib.decorator.retry.sleep'):
            assert reader.read() == UNSPECIFIED_COMPANY
