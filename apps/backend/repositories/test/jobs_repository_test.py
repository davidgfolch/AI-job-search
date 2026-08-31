import pytest
from unittest.mock import patch, MagicMock
from repositories.jobs_repository import JobsRepository
from commonlib.test.db_mock_util import create_mock_db


@pytest.fixture
def repo():
    return JobsRepository()


@pytest.fixture
def mock_db():
    return create_mock_db(
        count=50,
        fetchAll=[(1, "Job 1", "Company", "Remote", None, None, None, None, "2023-01-01", "2023-01-01")],
        columns=["id", "title", "company", "location", "salary", "url", "markdown", "web_page", "created", "modified"],
    )


def test_list_jobs_happy_path(repo, mock_db):
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.list_jobs(page=1, size=10)

    assert result["page"] == 1
    assert result["size"] == 10
    assert result["total"] == 50
    expected_item = dict(zip(
        ["id", "title", "company", "location", "salary", "url", "markdown", "web_page", "created", "modified"],
        (1, "Job 1", "Company", "Remote", None, None, None, None, "2023-01-01", "2023-01-01"),
    ))
    assert result["items"] == [expected_item]


def test_list_jobs_with_filters(repo, mock_db):
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.list_jobs(
            page=2, size=20, search="python", status="applied", order="salary asc", ids=[1, 2]
        )

    assert result["page"] == 2
    assert result["size"] == 20


def test_list_jobs_error_path(repo, mock_db):
    from mysql.connector.errors import DatabaseError

    mock_db.fetchAll.side_effect = DatabaseError("syntax error")
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.list_jobs(page=1, size=10, sql_filter="salary > 1000")

    assert "error" in result
    assert result["items"] == []
    assert result["total"] == 0


def test_count_jobs_happy_path(repo, mock_db):
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.count_jobs(status="applied")

    assert result == 50


def test_count_jobs_error_path(repo, mock_db):
    from mysql.connector.errors import DatabaseError

    mock_db.count.side_effect = DatabaseError("boom")
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.count_jobs(search="python")

    assert result == 0


def test_build_where(repo):
    where, params = repo.build_where(search="python", status="applied")

    assert isinstance(where, list)
    assert isinstance(params, list)


def test_fetch_jobs_without_columns(repo, mock_db):
    mock_db.fetchAll.side_effect = lambda query, params=None: None
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.list_jobs(page=1, size=10)

    assert result["items"] == []


def test_fetch_jobs_empty_columns(repo, mock_db):
    mock_db.fetchAll.side_effect = [
        [(1, "job")],
        [],
    ]
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.list_jobs(page=1, size=10)

    assert result["items"] == []


def test_update_job_found(mock_db):
    mock_db.fetchOne.return_value = (1,)
    repo = JobsRepository()
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.update_job(1, {"title": "New Title"})

    assert result == 1
    mock_db.executeAndCommit.assert_called_once()


def test_update_job_not_found(repo, mock_db):
    mock_db.fetchOne.return_value = None
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.update_job(99, {"title": "New Title"})

    assert result is None


def test_update_job_empty_data(mock_db):
    mock_db.fetchOne.return_value = (1,)
    repo = JobsRepository()
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.update_job(1, {})

    assert result == 1
    mock_db.executeAndCommit.assert_not_called()


def test_update_jobs_by_ids(repo, mock_db):
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.update_jobs_by_ids([1, 2, 3], {"ignored": True})

    assert result == 3
    mock_db.executeAndCommit.assert_called_once()


def test_update_jobs_by_ids_empty(repo, mock_db):
    with patch.object(repo, "get_db", return_value=mock_db):
        assert repo.update_jobs_by_ids([], {"ignored": True}) == 0
        assert repo.update_jobs_by_ids([1], {}) == 0

    mock_db.executeAndCommit.assert_not_called()


def test_update_jobs_by_filter(repo, mock_db):
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.update_jobs_by_filter(["1=1"], [], {"ignored": True})

    assert result == mock_db.executeAndCommit.return_value


def test_update_jobs_by_filter_empty(repo, mock_db):
    with patch.object(repo, "get_db", return_value=mock_db):
        assert repo.update_jobs_by_filter(["1=1"], [], {}) == 0

    mock_db.executeAndCommit.assert_not_called()


def test_create_job(repo, mock_db):
    with patch.object(repo, "get_db", return_value=mock_db):
        result = repo.create_job({"title": "Job"})

    assert result == mock_db.insertJob.return_value


def test_fetch_job_row_and_columns():
    default_db = create_mock_db(fetchOne=(1, "Job 1"))
    repo = JobsRepository()
    with patch.object(repo, "get_db", return_value=default_db):
        row = repo.fetch_job_row(default_db, 1)
        columns = repo.fetch_columns(default_db)

    assert row == (1, "Job 1")
    assert columns == ["id", "title", "company"]
