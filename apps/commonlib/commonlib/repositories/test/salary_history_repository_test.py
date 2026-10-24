import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from bson import ObjectId
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


def test_get_job_history_exposes_string_id(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    object_id = ObjectId()
    mock_col.find.return_value.sort.return_value.limit.return_value = [{"_id": object_id, "job_id": 1, "salary": "50k"}]
    result = repo.get_job_history(1)
    assert result == [{"id": str(object_id), "job_id": 1, "salary": "50k"}]


def test_get_company_history_direct_match(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    object_id = ObjectId()
    mock_col.find.return_value.sort.return_value.limit.return_value = [{"_id": object_id, "company": "Test"}]
    result = repo.get_company_history("Test")
    assert result == [{"id": str(object_id), "company": "Test"}]


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


def test_delete_record(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    mock_col.delete_one.return_value.deleted_count = 1
    object_id = ObjectId()
    assert repo.delete_record(str(object_id)) is True
    mock_mongo_provider.get_database.assert_called_with(write=True)
    mock_col.delete_one.assert_called_once_with({"_id": object_id})


def test_delete_record_not_found(repo, mock_mongo_provider):
    mock_col = MagicMock()
    mock_mongo_provider.get_database.return_value.__getitem__.return_value = mock_col
    mock_col.delete_one.return_value.deleted_count = 0
    assert repo.delete_record(str(ObjectId())) is False


def test_delete_record_invalid_id(repo, mock_mongo_provider):
    assert repo.delete_record("not-an-object-id") is False
    mock_mongo_provider.get_database.assert_not_called()


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
