import pytest
from unittest.mock import patch, MagicMock
from repositories.scrapper_state_repository import ScrapperStateRepository

STATE_DATA = {"Linkedin": {"keyword": "python"}, "Infojobs": {"keyword": "java"}}


@pytest.fixture
def mock_db():
    mock = MagicMock()
    mock.get_scrapper_state.return_value = STATE_DATA
    return mock


@pytest.fixture
def repo_with_mock(mock_db):
    repo = ScrapperStateRepository()
    with patch.object(repo, 'get_db', return_value=mock_db):
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        yield repo, mock_db


def test_get_all(repo_with_mock):
    repo, mock_db = repo_with_mock
    result = repo.get_all()
    assert result == STATE_DATA
    mock_db.get_scrapper_state.assert_called_once()


def test_replace_all(repo_with_mock):
    repo, mock_db = repo_with_mock
    result = repo.replace_all(STATE_DATA)
    assert result == STATE_DATA
    mock_db.update_scrapper_state.assert_called_once_with(STATE_DATA)
