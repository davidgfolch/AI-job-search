import pytest
from unittest.mock import MagicMock, patch
from repositories.jobWriteRepository import JobWriteRepository
from commonlib.test.db_mock_util import create_mock_db


@pytest.fixture
def repo():
    return JobWriteRepository()


def _mock_db(**kwargs):
    return create_mock_db(**kwargs)


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


@patch("repositories.jobWriteRepository.MysqlUtil")
@patch("repositories.jobWriteRepository.getConnection")
def test_update_job_not_found(mock_get_conn, mock_mysql_util_cls):
    mock_db = _mock_db(fetchOne=None)
    mock_mysql_util_cls.return_value = mock_db
    repo = JobWriteRepository()

    result = repo.update_job(99, {"title": "New Title"})

    assert result is None
    mock_db.executeAndCommit.assert_not_called()


@patch("repositories.jobWriteRepository.MysqlUtil")
@patch("repositories.jobWriteRepository.getConnection")
def test_update_job_empty_data(mock_get_conn, mock_mysql_util_cls):
    mock_db = _mock_db(fetchOne=(1,))
    mock_mysql_util_cls.return_value = mock_db
    repo = JobWriteRepository()

    result = repo.update_job(1, {})

    assert result == 1
    mock_db.executeAndCommit.assert_not_called()


@patch("repositories.jobWriteRepository.MysqlUtil")
@patch("repositories.jobWriteRepository.getConnection")
def test_update_jobs_by_ids(mock_get_conn, mock_mysql_util_cls):
    mock_db = _mock_db()
    mock_mysql_util_cls.return_value = mock_db
    repo = JobWriteRepository()

    result = repo.update_jobs_by_ids([1, 2, 3], {"ignored": True})

    assert result == 3
    mock_db.executeAndCommit.assert_called_once()
    query = mock_db.executeAndCommit.call_args[0][0]
    assert "id IN (%s, %s, %s)" in query


@patch("repositories.jobWriteRepository.MysqlUtil")
@patch("repositories.jobWriteRepository.getConnection")
def test_update_jobs_by_ids_empty(mock_get_conn, mock_mysql_util_cls):
    mock_db = _mock_db()
    mock_mysql_util_cls.return_value = mock_db
    repo = JobWriteRepository()

    assert repo.update_jobs_by_ids([], {"ignored": True}) == 0
    assert repo.update_jobs_by_ids([1], {}) == 0
    mock_db.executeAndCommit.assert_not_called()


@patch("repositories.jobWriteRepository.MysqlUtil")
@patch("repositories.jobWriteRepository.getConnection")
def test_update_jobs_by_filter(mock_get_conn, mock_mysql_util_cls):
    mock_db = _mock_db(executeAndCommit=5)
    mock_mysql_util_cls.return_value = mock_db
    repo = JobWriteRepository()

    result = repo.update_jobs_by_filter(["1=1", "status = %s"], ["applied"], {"ignored": True})

    assert result == 5
    query = mock_db.executeAndCommit.call_args[0][0]
    assert "UPDATE jobs SET" in query
    assert " WHERE 1=1 AND status = %s" in query


@patch("repositories.jobWriteRepository.MysqlUtil")
@patch("repositories.jobWriteRepository.getConnection")
def test_update_jobs_by_filter_empty(mock_get_conn, mock_mysql_util_cls):
    mock_db = _mock_db()
    mock_mysql_util_cls.return_value = mock_db
    repo = JobWriteRepository()

    result = repo.update_jobs_by_filter(["1=1"], [], {})

    assert result == 0
    mock_db.executeAndCommit.assert_not_called()


@patch("repositories.jobWriteRepository.MysqlUtil")
@patch("repositories.jobWriteRepository.getConnection")
def test_create_job(mock_get_conn, mock_mysql_util_cls):
    mock_db = _mock_db()
    mock_mysql_util_cls.return_value = mock_db
    repo = JobWriteRepository()

    result = repo.create_job({"title": "Job"})

    assert result == mock_db.insertJob.return_value
    mock_db.insertJob.assert_called_once_with({"title": "Job"})
