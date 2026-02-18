import pytest
from unittest.mock import MagicMock, patch
from repositories.jobReadRepository import JobReadRepository


@patch("repositories.jobReadRepository.MysqlUtil")
@patch("repositories.jobReadRepository.getConnection")
def test_list_jobs(mock_get_conn, mock_mysql_util_cls):
    repo = JobReadRepository()
    mock_db = MagicMock()
    mock_mysql_util_cls.return_value = mock_db
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)
    mock_db.count.return_value = 10
    mock_db.fetchAll.return_value = []

    result = repo.list_jobs(page=1, size=10)

    assert result["total"] == 10
