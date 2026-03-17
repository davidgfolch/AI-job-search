"""Tests for query_executor module."""
import pytest
from unittest.mock import MagicMock, patch
from commonlib.sql.query_executor import QueryExecutor


class TestQueryExecutor:
    """Tests for QueryExecutor class."""

    @pytest.fixture
    def mock_get_connection_ctx(self):
        """Mock get_connection_ctx function."""
        return MagicMock()

    @pytest.fixture
    def query_executor(self, mock_get_connection_ctx):
        """Create QueryExecutor instance with mock."""
        return QueryExecutor(mock_get_connection_ctx)

    def test_init(self, mock_get_connection_ctx):
        """Should initialize with get_connection_ctx function."""
        executor = QueryExecutor(mock_get_connection_ctx)
        assert executor._get_connection_ctx == mock_get_connection_ctx

    def test_count_returns_result(self, query_executor):
        """count should return the count value."""
        with patch.object(query_executor, '_execute_query') as mock_execute:
            mock_execute.return_value = 42
            result = query_executor.count('SELECT COUNT(*) FROM jobs')
            assert result == 42

    def test_fetch_one_returns_row(self, query_executor):
        """fetch_one should return a single row."""
        with patch.object(query_executor, '_execute_query') as mock_execute:
            expected_row = {'id': 1, 'title': 'Job'}
            mock_execute.return_value = expected_row
            result = query_executor.fetch_one('SELECT * FROM jobs WHERE id = %s', 1)
            assert result == expected_row

    def test_fetch_all_returns_rows(self, query_executor):
        """fetch_all should return all matching rows."""
        with patch.object(query_executor, '_execute_query') as mock_execute:
            expected_rows = [{'id': 1}, {'id': 2}]
            mock_execute.return_value = expected_rows
            result = query_executor.fetch_all('SELECT * FROM jobs')
            assert result == expected_rows

    def test_fetch_all_returns_none_on_error(self, query_executor):
        """fetch_all should return None on error."""
        with patch.object(query_executor, '_execute_query') as mock_execute:
            mock_execute.return_value = None
            result = query_executor.fetch_all('SELECT * FROM jobs')
            assert result is None

    def test_get_table_ddl_column_names_returns_columns(self, query_executor):
        """get_table_ddl_column_names should return list of column names."""
        with patch.object(query_executor, 'fetch_all') as mock_fetch:
            mock_fetch.return_value = [('id',), ('title',), ('company',)]
            with patch('commonlib.sql.query_executor.getColumnTranslated') as mock_translate:
                mock_translate.side_effect = lambda x: x
                result = query_executor.get_table_ddl_column_names('jobs')
                assert result == ['id', 'title', 'company']

    def test_execute_query_raises_exception(self, query_executor):
        """_execute_query should propagate exception."""
        with patch.object(query_executor, '_get_cursor') as mock_cursor:
            mock_cursor.side_effect = Exception('DB error')
            with pytest.raises(Exception, match='DB error'):
                query_executor._execute_query(lambda c: c.execute('SELECT 1'))
