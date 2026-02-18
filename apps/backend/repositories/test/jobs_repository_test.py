import pytest
from unittest.mock import patch, MagicMock
from repositories.jobWriteRepository import JobWriteRepository
from commonlib.db_mock_util import create_mock_db


@patch("repositories.jobWriteRepository.MysqlUtil")
@patch("repositories.jobWriteRepository.getConnection")
def test_update_jobs_by_filter_uses_return_value(mock_get_conn, mock_mysql_util_cls):
    """
    Verify that update_jobs_by_filter returns the result of executeAndCommit
    instead of trying to access db.cursor.rowcount.
    """
    mock_db_instance = create_mock_db(executeAndCommit=42)
    mock_mysql_util_cls.return_value = mock_db_instance

    expected_rowcount = 42

    repo = JobWriteRepository()

    update_data = {"ignored": True}
    where_clauses = ["1=1"]
    params = []

    result = repo.update_jobs_by_filter(where_clauses, params, update_data)

    mock_db_instance.executeAndCommit.assert_called_once()
    assert result == expected_rowcount
