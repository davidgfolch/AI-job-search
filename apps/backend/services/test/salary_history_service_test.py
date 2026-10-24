from unittest.mock import patch

from services.salary_history_service import SalaryHistoryService


def test_service_imports():
    assert SalaryHistoryService is not None


@patch("services.salary_history_service._repo")
def test_delete_record_delegates_to_repository(mock_repo):
    mock_repo.delete_record.return_value = True
    assert SalaryHistoryService().delete_record("abc") is True
    mock_repo.delete_record.assert_called_once_with("abc")
