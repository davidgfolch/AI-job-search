import pytest
from unittest.mock import MagicMock
from scrapper.navigator.tecnoempleoNavigator import TecnoempleoNavigator


@pytest.fixture
def mock_selenium():
    return MagicMock()


@pytest.fixture
def navigator(mock_selenium):
    return TecnoempleoNavigator(mock_selenium, False)