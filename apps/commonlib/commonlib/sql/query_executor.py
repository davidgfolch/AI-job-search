from typing import TypeVar, Union, Sequence, Dict
from mysql.connector.types import RowItemType
from mysql.connector import MySQLConnection
import mysql.connector as mysqlConnector
from contextlib import contextmanager

from commonlib.sqlUtil import getColumnTranslated
from ..terminalColor import green
from .connection_manager import get_connection

T = TypeVar("T")


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
        return self._execute_query(lambda c: (c.execute(query, params), c.fetchone()[0])[1])

    def fetch_one(self, query: str, id: int | str) -> Dict[str, RowItemType]:
        """
        Fetch a single row by ID.

        Args:
            query: SQL query with single placeholder
            id: ID parameter for the query

        Returns:
            Row dict or None on error
        """
        return self._execute_query(lambda c: (c.execute(query, [id]), c.fetchone())[1])

    def fetch_all(self, query: str, params: tuple = None) -> list:
        """
        Fetch all rows matching the query.

        Args:
            query: SQL query
            params: Optional query parameters

        Returns:
            List of rows or None on error
        """
        return self._execute_query(lambda c: (c.execute(query, params), c.fetchall())[1])

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
                    print(green(f'Updated database: {params}'), flush=True)
                else:
                    from commonlib.sqlUtil import error
                    error(Exception('No rows affected'))

            self._execute_transaction(op)

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

    def _execute_query(self, callback: callable):
        """Execute a query callback with cursor management."""
        with self._get_cursor() as (_, cursor):
            return callback(cursor)

    def _execute_transaction(self, callback: callable):
        """Execute a callback within a transaction."""
        with self._get_cursor() as (conn, cursor):
            try:
                result = callback(cursor)
                conn.commit()
                return result
            except Exception as ex:
                conn.rollback()
                raise ex

    @contextmanager
    def _get_cursor(self):
        """Get cursor from pool connection, closing is handled by connection context."""
        with self._get_connection_ctx() as conn:
            if not conn.is_connected():
                print(f'Reconnecting to DB conn: {conn}', flush=True)
                conn.reconnect()
            cursor = conn.cursor()
            cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;')
            try:
                yield conn, cursor
            finally:
                cursor.close()
