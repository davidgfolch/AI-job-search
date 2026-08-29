import pytest
from unittest.mock import MagicMock
from commonlib.repositories.cron_state_repository import CronStateRepository


@pytest.fixture
def mock_mongo_provider():
    return MagicMock()


@pytest.fixture
def repo(mock_mongo_provider):
    return CronStateRepository(mock_mongo_provider)


def test_get_state_found(repo, mock_mongo_provider):
    mock_col = mock_mongo_provider.get_database.return_value.__getitem__.return_value
    mock_col.find_one.return_value = {"_id": "job1", "last_run": "2024-01-01"}
    result = repo.get_state("job1")
    assert result == {"last_run": "2024-01-01"}
    assert "_id" not in result


def test_get_state_not_found(repo, mock_mongo_provider):
    mock_col = mock_mongo_provider.get_database.return_value.__getitem__.return_value
    mock_col.find_one.return_value = None
    result = repo.get_state("nonexistent")
    assert result is None


def test_update_state(repo, mock_mongo_provider):
    mock_col = mock_mongo_provider.get_database.return_value.__getitem__.return_value
    repo.update_state("job1", {"last_run": "2024-01-01"})
    mock_col.update_one.assert_called_once_with(
        {"_id": "job1"}, {"$set": {"last_run": "2024-01-01"}}, upsert=True
    )
