import pytest
from unittest.mock import patch
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
            service.delete_repo, "update_jobs_by_filter"
        ) as mock_update_filter,
        patch.object(service.delete_repo, "update_jobs_by_ids") as mock_update_ids,
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
