import pytest
from repositories.queries.repository_utils import execute_with_error_handler


def test_execute_with_error_handler_success():
    def callback():
        return {"result": "success"}

    result = execute_with_error_handler(None, "SELECT 1", [], callback)
    assert result == {"result": "success"}


def test_execute_with_error_handler_with_items():
    def callback():
        return {"items": [1, 2, 3], "total": 3}

    result = execute_with_error_handler(None, "SELECT 1", [], callback, include_items=True)
    assert result == {"items": [1, 2, 3], "total": 3}
