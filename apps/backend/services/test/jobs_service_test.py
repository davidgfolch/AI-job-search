import pytest
from unittest.mock import patch, MagicMock
from services.jobs_service import JobsService
from api.jobs import BulkJobUpdate, JobUpdate


@patch("services.jobs_service.JobsRepository")
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
    mock_repo_cls,
    update_data,
    ids,
    filters,
    select_all,
    expected_count,
    expected_where,
    expected_params,
):
    """Test bulk update operations"""
    mock_repo = mock_repo_cls.return_value
    service = JobsService(repo=mock_repo)
    if select_all:
        # Mock build_where return for select_all tests
        mock_repo.build_where.return_value = (expected_where, expected_params)
        # Mock update return
        mock_repo.update_jobs_by_filter.return_value = expected_count
    else:
        # Mock return for ID-based tests
        mock_repo.update_jobs_by_ids.return_value = expected_count
    count = service.bulk_update_jobs(update_data=update_data, ids=ids, filters=filters, select_all=select_all)
    assert count == expected_count
    if select_all:
        mock_repo.build_where.assert_called_once()
        mock_repo.update_jobs_by_filter.assert_called_once()
        args, _ = mock_repo.update_jobs_by_filter.call_args
        assert args[0] == expected_where
        assert args[1] == expected_params
        assert args[2] == update_data
    else:
        mock_repo.update_jobs_by_ids.assert_called_once_with(ids, update_data)
        mock_repo.build_where.assert_not_called()
        mock_repo.update_jobs_by_filter.assert_not_called()
