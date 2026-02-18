import pytest
from unittest.mock import MagicMock, patch
from repositories.jobWriteRepository import JobWriteRepository


@patch("repositories.jobWriteRepository.MysqlUtil")
@patch("repositories.jobWriteRepository.getConnection")
def test_update_job(mock_get_conn, mock_mysql_util_cls):
    repo = JobWriteRepository()
    mock_db = MagicMock()
    mock_mysql_util_cls.return_value = mock_db
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)
    mock_db.fetchOne.return_value = (1,)

    result = repo.update_job(1, {"title": "New Title"})

    assert result == 1
    mock_db.executeAndCommit.assert_called_once()
