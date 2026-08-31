import pytest
from unittest.mock import patch, MagicMock
from services.jobs_service import JobsService
from api.jobs import BulkJobUpdate, JobUpdate


@pytest.mark.parametrize(
    "update_data,ids,filters,select_all,expected_count,expected_where,expected_params",
    [
        ({"ignored": True}, [1, 2, 3], None, False, 3, None, None),
        (
            {"ignored": True},
            None,
            {"search": "python", "ignored": False},
            True,
            10,
            ["search LIKE %s", "ignored = 0"],
            ["%python%"],
        ),
    ],
)
def test_bulk_update_jobs(
    update_data,
    ids,
    filters,
    select_all,
    expected_count,
    expected_where,
    expected_params,
):
    """Test bulk update operations"""
    service = JobsService()
    with (
        patch("services.jobs_service.build_jobs_where_clause") as mock_build_where,
        patch.object(
            service.delete_service, "update_jobs_by_filter"
        ) as mock_update_filter,
        patch.object(service.delete_service, "update_jobs_by_ids") as mock_update_ids,
    ):
        if select_all:
            mock_build_where.return_value = (expected_where, expected_params)
            mock_update_filter.return_value = expected_count
        else:
            mock_update_ids.return_value = expected_count
        count = service.bulk_update_jobs(
            update_data=update_data, ids=ids, filters=filters, select_all=select_all
        )
        assert count == expected_count
        if select_all:
            mock_build_where.assert_called_once()
            mock_update_filter.assert_called_once()
            args, _ = mock_update_filter.call_args
            assert args[0] == expected_where
            assert args[1] == expected_params
            assert args[2] == update_data
        else:
            mock_update_ids.assert_called_once_with(ids, update_data)
            mock_build_where.assert_not_called()
            mock_update_filter.assert_not_called()


def test_bulk_update_jobs_neither():
    service = JobsService()
    with (
        patch.object(service.delete_service, "update_jobs_by_filter") as mock_update_filter,
        patch.object(service.delete_service, "update_jobs_by_ids") as mock_update_ids,
    ):
        count = service.bulk_update_jobs(update_data={"ignored": True})

        assert count == 0
        mock_update_filter.assert_not_called()
        mock_update_ids.assert_not_called()


def test_delete_jobs_by_ids():
    service = JobsService()
    with patch.object(service.delete_service, "delete_by_ids", return_value=4) as mock_delete:
        count = service.delete_jobs(ids=[1, 2])

    assert count == 4
    mock_delete.assert_called_once_with([1, 2])


def test_delete_jobs_by_filters():
    service = JobsService()
    with patch.object(service.delete_service, "delete_by_filters", return_value=9) as mock_delete:
        count = service.delete_jobs(filters={"search": "python"}, select_all=True)

    assert count == 9
    mock_delete.assert_called_once_with({"search": "python"})


def test_delete_jobs_neither():
    service = JobsService()
    with (
        patch.object(service.delete_service, "delete_by_ids") as mock_ids,
        patch.object(service.delete_service, "delete_by_filters") as mock_filters,
    ):
        count = service.delete_jobs()

    assert count == 0
    mock_ids.assert_not_called()
    mock_filters.assert_not_called()


def test_list_jobs():
    service = JobsService()
    with patch.object(service.repo, "list_jobs", return_value={"items": [], "total": 0}) as mock_list:
        result = service.list_jobs(page=1, size=20, search="python")

    assert result == {"items": [], "total": 0}
    mock_list.assert_called_once()
    assert mock_list.call_args[1]["page"] == 1
    assert mock_list.call_args[1]["size"] == 20


def test_count_jobs():
    service = JobsService()
    with patch.object(service.repo, "count_jobs", return_value=42) as mock_count:
        result = service.count_jobs(status="applied")

    assert result == 42
    mock_count.assert_called_once()


def test_get_job_found():
    service = JobsService()
    mock_db = MagicMock()
    mock_db.__enter__.return_value = mock_db
    with (
        patch.object(service.repo, "get_db", return_value=mock_db),
        patch.object(service.repo, "fetch_job_row", return_value=(1, "Job", "Acme")),
        patch.object(service.repo, "fetch_columns", return_value=["id", "title", "company"]),
        patch("services.jobs_service.CompanySynonymService") as mock_synonym_cls,
    ):
        mock_synonym_cls.return_value.get_synonyms.return_value = ["Acme Corp"]
        result = service.get_job(1)

    assert result["id"] == 1
    assert result["synonyms"] == ["Acme Corp"]


def test_get_job_not_found():
    service = JobsService()
    mock_db = MagicMock()
    mock_db.__enter__.return_value = mock_db
    with (
        patch.object(service.repo, "get_db", return_value=mock_db),
        patch.object(service.repo, "fetch_job_row", return_value=None),
    ):
        result = service.get_job(1)

    assert result is None


def test_get_job_no_company():
    service = JobsService()
    mock_db = MagicMock()
    mock_db.__enter__.return_value = mock_db
    with (
        patch.object(service.repo, "get_db", return_value=mock_db),
        patch.object(service.repo, "fetch_job_row", return_value=(1, "Job", None)),
        patch.object(service.repo, "fetch_columns", return_value=["id", "title", "company"]),
    ):
        result = service.get_job(1)

    assert result["company"] is None
    assert "synonyms" not in result


def test_snapshot_service_lazy():
    service = JobsService()
    assert service._snapshot_service is None
    snap_service = service.snapshot_service
    assert service._snapshot_service is snap_service
    assert service.snapshot_service is snap_service


def test_create_job():
    service = JobsService()
    with (
        patch.object(service.repo, "create_job", return_value=5) as mock_create,
        patch.object(service, "get_job", return_value={"id": 5, "job_id": "manual-123"}) as mock_get,
    ):
        result = service.create_job({"title": "Job"})

    assert result == {"id": 5, "job_id": "manual-123"}
    mock_get.assert_called_once_with(5)
    generated_job = mock_create.call_args[0][0]
    assert "manual-" in generated_job["job_id"]


def test_create_job_with_job_id():
    service = JobsService()
    with (
        patch.object(service.repo, "create_job", return_value=5) as mock_create,
        patch.object(service, "get_job", return_value=None),
    ):
        result = service.create_job({"title": "Job", "job_id": "existing-1"})

    assert result is None
    assert mock_create.call_args[0][0]["job_id"] == "existing-1"


def test_update_job_creates_snapshot():
    from services.jobSnapshotService import JobSnapshotService

    service = JobsService()
    old_job = {"id": 1, "applied": False, "title": "Job"}
    updated_job = {"id": 1, "applied": True, "title": "Job"}
    mock_snapshot = MagicMock(spec=JobSnapshotService)
    service._snapshot_service = mock_snapshot
    with (
        patch.object(service, "get_job", side_effect=[old_job, updated_job]),
        patch.object(service.repo, "update_job", return_value=1),
    ):
        result = service.update_job(1, {"applied": True})

    assert result == updated_job
    mock_snapshot.maybe_create_snapshot_on_update.assert_called_once_with(old_job, {"applied": True})


def test_update_job_missing():
    service = JobsService()
    with (
        patch.object(service, "get_job", return_value=None),
        patch.object(service.repo, "update_job", return_value=None),
    ):
        result = service.update_job(999, {"applied": True})

    assert result is None
