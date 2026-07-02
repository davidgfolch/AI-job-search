import pytest
from unittest.mock import MagicMock, patch
from services.job_delete_service import JobDeleteService
from repositories.jobDeleteRepository import JobDeleteRepository
from commonlib.jobSnapshotRepository import JobSnapshotRepository


@pytest.fixture
def mock_repo():
    return MagicMock(spec=JobDeleteRepository)


@pytest.fixture
def mock_get_job():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    with patch("services.job_delete_service.JobDeleteRepository", return_value=mock_repo):
        s = JobDeleteService()
    s.delete_repo = mock_repo
    return s


@pytest.fixture
def service_with_callback(mock_repo, mock_get_job):
    with patch("services.job_delete_service.JobDeleteRepository", return_value=mock_repo):
        s = JobDeleteService(get_job_callback=mock_get_job)
    s.delete_repo = mock_repo
    return s


def test_build_snapshot_queries(service):
    jobs = [
        {"jobId": "1", "title": "Engineer", "company": "A", "web_page": "linkedin"},
        {"jobId": "2", "title": "Designer", "company": "B", "web_page": "infojobs"},
    ]
    with patch.object(JobSnapshotRepository, "build_snapshot_query_and_params", side_effect=[
        ("INSERT INTO snapshots ...", ("1", "DELETED")),
        ("INSERT INTO snapshots ...", ("2", "DELETED")),
    ]) as mock_build:
        result = service._build_snapshot_queries(jobs)
        assert len(result) == 2
        assert mock_build.call_count == 2
        mock_build.assert_any_call(jobs[0], "DELETED")
        mock_build.assert_any_call(jobs[1], "DELETED")


def test_delete_by_filters(service, mock_repo):
    mock_repo.get_jobs_by_filter.return_value = [{"jobId": "1"}, {"jobId": "2"}]
    mock_repo.delete_jobs_with_snapshots.return_value = 2

    with patch("services.job_delete_service.extract_filter_params") as mock_extract, \
         patch("services.job_delete_service.build_jobs_where_clause") as mock_build_where:
        mock_extract.return_value = {"search": "python"}
        mock_build_where.return_value = (["search LIKE %s"], ["%python%"])

        result = service.delete_by_filters({"search": "python"})

        assert result == 2
        mock_repo.get_jobs_by_filter.assert_called_once_with(["search LIKE %s"], ["%python%"])
        mock_repo.delete_jobs_with_snapshots.assert_called_once()


def test_delete_by_ids_with_callback(service_with_callback, mock_repo, mock_get_job):
    mock_get_job.side_effect = [
        {"jobId": "1", "title": "Engineer"},
        None,
        {"jobId": "3", "title": "Designer"},
    ]
    mock_repo.delete_jobs_with_snapshots.return_value = 2

    with patch.object(JobSnapshotRepository, "build_snapshot_query_and_params", return_value=("q", ("p",))):
        result = service_with_callback.delete_by_ids([1, 2, 3])

        assert result == 2
        assert mock_get_job.call_count == 3
        mock_get_job.assert_any_call(1)
        mock_get_job.assert_any_call(2)
        mock_get_job.assert_any_call(3)


def test_delete_by_ids_no_callback(service, mock_repo):
    mock_repo.delete_jobs_with_snapshots.return_value = 0
    result = service.delete_by_ids([1, 2])
    assert result == 0


@pytest.mark.parametrize("ids,update_data,expected", [
    ([1, 2], {"ignored": True}, 2),
    ([5], {"status": "applied"}, 1),
    ([], {"ignored": True}, 0),
])
def test_update_jobs_by_ids(service, mock_repo, ids, update_data, expected):
    mock_repo.update_jobs_by_ids.return_value = expected
    result = service.update_jobs_by_ids(ids, update_data)
    assert result == expected
    mock_repo.update_jobs_by_ids.assert_called_once_with(ids, update_data)


def test_update_jobs_by_filter(service, mock_repo):
    mock_repo.update_jobs_by_filter.return_value = 5
    result = service.update_jobs_by_filter(["search LIKE %s"], ["%python%"], {"ignored": True})
    assert result == 5
    mock_repo.update_jobs_by_filter.assert_called_once_with(
        ["search LIKE %s"], ["%python%"], {"ignored": True}
    )
