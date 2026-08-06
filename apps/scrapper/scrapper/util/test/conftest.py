import pytest
from unittest.mock import MagicMock
from scrapper.util.persistence_manager import PersistenceManager


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.get_all.return_value = {"Site": {"keyword": "python"}}
    return repo


@pytest.fixture
def manager(mock_repo):
    return PersistenceManager(repository=mock_repo)
