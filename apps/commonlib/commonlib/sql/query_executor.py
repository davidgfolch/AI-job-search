from typing import TypeVar, Union, Sequence, Dict
from mysql.connector.types import RowItemType
import mysql.connector as mysqlConnector
from contextlib import contextmanager
import os
import time

from commonlib.sqlUtil import getColumnTranslated
from ..observability import get_logger

logger = get_logger("query_executor")

T = TypeVar("T")

SLOW_QUERY_MS_ENV = "COMMONLIB_DB_SLOW_QUERY_MS"
DEFAULT_SLOW_QUERY_MS = 200.0
SLOW_QUERY_MAX_CHARS = 200


def slow_query_threshold_ms() -> float:
    """`COMMONLIB_DB_SLOW_QUERY_MS`, or the default when unset or unparsable.

    Zero or a negative value disables the slow-query record entirely.
    """
    raw = (os.getenv(SLOW_QUERY_MS_ENV, "") or "").strip()
    if not raw:
        return DEFAULT_SLOW_QUERY_MS
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_SLOW_QUERY_MS


def _log_slow_query(query: str, started_at: float, operation: str) -> None:
    """Emit `db.query_slow` for a statement that outlived the threshold.

    The SQL is collapsed to one line and truncated, and parameters are left out
    because they carry search terms and scraped content.
    """
    threshold = slow_query_threshold_ms()
    if threshold <= 0:
        return
    duration_ms = (time.perf_counter() - started_at) * 1000
    if duration_ms < threshold:
        return
    logger.warning("db.query_slow", operation=operation, duration_ms=round(duration_ms, 1), query=" ".join(query.split())[:SLOW_QUERY_MAX_CHARS])


class QueryExecutor:
    """Executes database queries including fetch and count operations."""

    def __init__(self, get_connection_ctx: callable):
        self._get_connection_ctx = get_connection_ctx

    def count(self, query: str, params: Union[Sequence[T], Dict[str, T]] = ()) -> int:
        """
        Execute a COUNT query and return the result.

        Args:
            query: SQL query with placeholders
            params: Query parameters

        Returns:
            Count value or None on error
        """
        return self._execute_query(lambda c: (c.execute(query, params), c.fetchone()[0])[1], query, "count")

    def fetch_one(self, query: str, id: int | str) -> Dict[str, RowItemType]:
        """
        Fetch a single row by ID.

        Args:
            query: SQL query with single placeholder
            id: ID parameter for the query

        Returns:
            Row dict or None on error
        """
        return self._execute_query(lambda c: (c.execute(query, [id]), c.fetchone())[1], query, "fetch_one")

    def fetch_all(self, query: str, params: tuple = None) -> list:
        """
        Fetch all rows matching the query.

        Args:
            query: SQL query
            params: Optional query parameters

        Returns:
            List of rows or None on error
        """
        return self._execute_query(lambda c: (c.execute(query, params), c.fetchall())[1], query, "fetch_all")

    def fetch_all_with_columns(self, query: str, params: tuple = None) -> tuple[list[str], list]:
        """Fetch all rows plus the column names of the executed SELECT.

        `cursor.column_names` comes from the statement itself, so callers that need
        dict rows do not run a second `SHOW COLUMNS` round trip per request.
        """
        def op(cursor):
            cursor.execute(query, params)
            return list(cursor.column_names or []), cursor.fetchall()
        return self._execute_query(op, query, "fetch_all_with_columns")

    def update_from_ai(self, query: str, params: tuple) -> None:
        """
        Execute an update query with retry logic.

        Args:
            query: UPDATE SQL query
            params: Query parameters

        Raises:
            mysqlConnector.Error: On failure after retries
        """
        from ..decorator.retry import retry

        @retry(retries=5, delay=1, exception=mysqlConnector.Error)
        def _update():
            def op(cursor):
                cursor.execute(query, params)
                if cursor.rowcount > 0:
                    logger.info("db.updated", params=params)
                else:
                    from commonlib.sqlUtil import error
                    error(Exception('No rows affected'))

            self._execute_transaction(op, query, "update_from_ai")

        _update()

    def get_table_ddl_column_names(self, table: str) -> list[str]:
        """
        Get column names from table DDL in SELECT order.

        Args:
            table: Table name

        Returns:
            List of column names
        """
        columns = self.fetch_all(f'SHOW COLUMNS FROM `{table}`')
        columns = [c[0] for c in columns]
        columns = [getColumnTranslated(c) for c in columns]
        return columns

    def _execute_query(self, callback: callable, query: str = "", operation: str = "query"):
        """Execute a query callback with cursor management, timing it for the slow log."""
        started_at = time.perf_counter()
        try:
            with self._get_cursor() as (_, cursor):
                return callback(cursor)
        finally:
            if query:
                _log_slow_query(query, started_at, operation)

    def _execute_transaction(self, callback: callable, query: str = "", operation: str = "transaction"):
        """Execute a callback within a transaction, timing it for the slow log."""
        started_at = time.perf_counter()
        try:
            with self._get_cursor() as (conn, cursor):
                try:
                    result = callback(cursor)
                    conn.commit()
                    return result
                except Exception as ex:
                    conn.rollback()
                    raise ex
        finally:
            if query:
                _log_slow_query(query, started_at, operation)

    @contextmanager
    def _get_cursor(self):
        """Get cursor from pool connection, closing is handled by connection context."""
        with self._get_connection_ctx() as conn:
            if not conn.is_connected():
                logger.info("db.reconnecting", conn=str(conn))
                conn.reconnect()
            cursor = conn.cursor()
            cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;')
            try:
                yield conn, cursor
            finally:
                cursor.close()
