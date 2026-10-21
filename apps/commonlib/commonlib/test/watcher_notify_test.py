from unittest.mock import MagicMock, patch

import pytest

from commonlib.watcher_notify import NOTIFY_PATH, notify_watcher

BASE_URL = "http://backend:8000"


def _response(ok=True, status_code=200):
    response = MagicMock()
    response.ok = ok
    response.status_code = status_code
    return response


@patch("commonlib.watcher_notify.requests.post")
def test_posts_ids_with_event_type_and_timeout(mock_post):
    mock_post.return_value = _response()

    assert notify_watcher([1, 2], BASE_URL) is True

    mock_post.assert_called_once_with(
        f"{BASE_URL}{NOTIFY_PATH}",
        json={"ids": [1, 2], "event_type": "jobs_enriched"},
        timeout=5,
    )


@patch("commonlib.watcher_notify.requests.post")
def test_trims_trailing_slash_from_base_url(mock_post):
    mock_post.return_value = _response()

    notify_watcher([3], f"{BASE_URL}/")

    assert mock_post.call_args.args[0] == f"{BASE_URL}{NOTIFY_PATH}"


@patch("commonlib.watcher_notify.requests.post")
def test_custom_event_type_and_timeout(mock_post):
    mock_post.return_value = _response()

    notify_watcher([4], BASE_URL, event_type="job_updated", timeout=1.5)

    mock_post.assert_called_once_with(
        f"{BASE_URL}{NOTIFY_PATH}",
        json={"ids": [4], "event_type": "job_updated"},
        timeout=1.5,
    )


@pytest.mark.parametrize("ids", [[], (), iter([])])
@patch("commonlib.watcher_notify.requests.post")
def test_empty_ids_skip_request(mock_post, ids):
    assert notify_watcher(ids, BASE_URL) is True
    mock_post.assert_not_called()


@patch("commonlib.watcher_notify.logger")
@patch("commonlib.watcher_notify.requests.post", side_effect=RuntimeError("boom"))
def test_connection_failure_is_logged_and_returns_false(mock_post, mock_logger):
    assert notify_watcher([9], BASE_URL) is False

    mock_logger.warning.assert_called_once_with(
        "watcher.notify_failed", job_ids=[9], error="boom"
    )


@patch("commonlib.watcher_notify.logger")
@patch("commonlib.watcher_notify.requests.post")
def test_rejected_response_is_logged_and_returns_false(mock_post, mock_logger):
    mock_post.return_value = _response(ok=False, status_code=500)

    assert notify_watcher([10], BASE_URL) is False

    mock_logger.warning.assert_called_once_with(
        "watcher.notify_rejected", job_ids=[10], status_code=500, base_url=BASE_URL
    )
