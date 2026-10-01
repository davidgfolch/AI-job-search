import pytest
import mysql
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


@pytest.mark.parametrize("error_text,expected_syntax", [
    ("You have an error in your SQL syntax near 'FROMM'", True),
    ("Lost connection to MySQL server during query", False),
], ids=["syntax", "connection"])
def test_database_error_is_logged_without_bind_values(error_text, expected_syntax, log_records):
    def callback():
        raise mysql.connector.errors.ProgrammingError(msg=error_text)

    result = execute_with_error_handler(None, "WHERE secret_column = %s", ["secret-value"], callback)

    assert result == 0
    records = log_records(event="db.query_failed")
    assert len(records) == 1
    assert records[0]["level"] == "error"
    assert records[0]["error"] == "ProgrammingError"
    assert records[0]["syntax_error"] is expected_syntax
    assert records[0]["include_items"] is False
    assert "secret_column" not in str(records[0])
    assert "secret-value" not in str(records[0])


def test_database_error_with_items_returns_error_payload(log_records):
    def callback():
        raise mysql.connector.errors.ProgrammingError(msg="syntax error")

    result = execute_with_error_handler(None, "WHERE 1", [], callback, include_items=True)

    assert result["items"] == []
    assert result["total"] == 0
    assert "syntax error" in result["error"]
    assert log_records(event="db.query_failed")[0]["include_items"] is True
