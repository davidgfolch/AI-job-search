import pytest
from unittest.mock import MagicMock
from commonlib.findLastDuplicated import find_last_duplicated


@pytest.mark.parametrize("title,company,url", [
    ("Software Engineer", "Joppy", None),
    ("", "Tech Corp", None),
    ("Title", "", None),
])
def test_find_last_duplicated_early_returns(title, company, url):
    mock_mysql = MagicMock()
    result = find_last_duplicated(mock_mysql, title, company, url)
    assert result is None
    mock_mysql.fetchAll.assert_not_called()


@pytest.mark.parametrize("title,company,url,expected_id,expected_params", [
    ("Software Engineer", "Tech Corp", None, 123, ["Software Engineer", "Tech Corp"]),
    ("Software Engineer", "Tech Corp", "https://example.com/job/123", 456, ["Software Engineer", "Tech Corp", "https://example.com/job/123"]),
    ("", "", "https://example.com/job/123", 789, ["https://example.com/job/123"]),
    ("Dev", "Co", None, 101, ["Dev", "Co"]),
    ("Engineer", "Joppy", "https://example.com/job/999", 888, ["https://example.com/job/999"]),
])
def test_find_last_duplicated_found(title, company, url, expected_id, expected_params):
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.return_value = [(expected_id,)]
    result = find_last_duplicated(mock_mysql, title, company, url)
    assert result == expected_id
    mock_mysql.fetchAll.assert_called_once()
    args = mock_mysql.fetchAll.call_args[0]
    assert args[1] == tuple(expected_params)


def test_find_last_duplicated_not_found():
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.return_value = []
    result = find_last_duplicated(mock_mysql, "Software Engineer", "Tech Corp")
    assert result is None


@pytest.mark.parametrize("title,company,url,should_contain,should_not_contain", [
    ("Software Engineer", "Tech Corp", None, "title = %s AND company = %s", "url"),
    ("Software Engineer", "Tech Corp", "https://example.com/job/123", "(title = %s AND company = %s) OR (url IS NOT NULL AND url = %s)", None),
    ("", "", "https://example.com/job/123", "url IS NOT NULL AND url = %s", "title = %s AND company = %s"),
    ("Engineer", "Joppy", "https://example.com/job/999", "url IS NOT NULL AND url = %s", "title = %s AND company = %s"),
])
def test_find_last_duplicated_sql_conditions(title, company, url, should_contain, should_not_contain):
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.return_value = []
    find_last_duplicated(mock_mysql, title, company, url)
    query = mock_mysql.fetchAll.call_args[0][0]
    assert should_contain in query
    if should_not_contain:
        assert should_not_contain not in query


def test_find_last_duplicated_same_title_different_company_not_duplicate():
    mock_mysql = MagicMock()
    mock_mysql.fetchAll.return_value = []
    result = find_last_duplicated(mock_mysql, "Backend Engineer", "Incode", "https://linkedin.com/jobs/view/123/")
    assert result is None
    query = mock_mysql.fetchAll.call_args[0][0]
    assert "(title = %s AND company = %s)" in query
    assert "OR" in query
