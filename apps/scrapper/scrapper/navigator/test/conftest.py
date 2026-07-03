import pytest
from unittest.mock import MagicMock
from scrapper.navigator.linkedinNavigator import LinkedinNavigator


@pytest.fixture
def mock_selenium():
    return MagicMock()


@pytest.fixture
def navigator(mock_selenium):
    return LinkedinNavigator(mock_selenium, False)
