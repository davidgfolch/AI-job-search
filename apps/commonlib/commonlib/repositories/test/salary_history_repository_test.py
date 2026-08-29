import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from commonlib.repositories.salary_history_repository import SalaryHistoryRepository


@pytest.fixture
def mock_mongo_provider():
    return MagicMock()


@pytest.fixture
def repo(mock_mongo_provider):
    return SalaryHistoryRepository(mock_mongo_provider)


def test_get_job_history(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    mock_col.find.return_value.sort.return_value.limit.return_value = [{"job_id": 1}]
    result = repo.get_job_history(1)
    assert len(result) == 1
    mock_col.find.assert_called_once()


def test_get_company_history_direct_match(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    mock_col.find.return_value.sort.return_value.limit.return_value = [{"company": "Test"}]
    result = repo.get_company_history("Test")
    assert len(result) == 1


def test_get_company_history_fallback_to_candidate(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    mock_col.find.return_value.sort.return_value.limit.side_effect = [[], [{"company": "Candidate"}]]
    with patch("commonlib.repositories.salary_history_repository.get_best_candidate", return_value="Best"):
        result = repo.get_company_history("Test")
        assert len(result) == 1


def test_get_company_history_no_results(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    mock_col.find.return_value.sort.return_value.limit.return_value = []
    with patch("commonlib.repositories.salary_history_repository.get_best_candidate", return_value=None):
        result = repo.get_company_history("Test")
        assert result == []


def test_get_last_record(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    mock_col.find_one.return_value = {"job_id": 1, "salary": "50k"}
    result = repo.get_last_record(1)
    assert result["salary"] == "50k"


def test_get_last_record_none(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    mock_col.find_one.return_value = None
    result = repo.get_last_record(999)
    assert result is None


def test_record_exists_true(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    mock_col.find_one.return_value = {"job_id": 1}
    result = repo.record_exists(1, "50k", datetime.now())
    assert result is True


def test_record_exists_false(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    mock_col.find_one.return_value = None
    result = repo.record_exists(1, "50k", datetime.now())
    assert result is False


def test_save_record(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    repo.save_record({"job_id": 1, "salary": "50k"})
    mock_col.insert_one.assert_called_once()


def test_save_records_success(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    mock_col.insert_many.return_value.inserted_ids = [1, 2]
    result = repo.save_records([{"a": 1}, {"a": 2}])
    assert result == 2


def test_save_records_empty(repo):
    result = repo.save_records([])
    assert result == 0


def test_save_records_exception(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    mock_col.insert_many.side_effect = Exception("dup key")
    result = repo.save_records([{"a": 1}])
    assert result == 0
