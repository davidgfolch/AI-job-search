from typing import Callable, Any
import mysql.connector as mysqlConnector
from mysql.connector import MySQLConnection
from contextlib import contextmanager

from commonlib.sqlUtil import error
from ..terminalColor import red, yellow


class TransactionManager:
    """Handles database transactions including rollback and commit operations."""

    def __init__(self, get_connection: Callable[[], MySQLConnection]):
        self._get_connection = get_connection

    def execute_transaction(self, callback: Callable) -> Any:
        """
        Execute a callback within a transaction.

        Args:
            callback: Function that receives a cursor and returns result

        Returns:
            Result from callback, or None on error
        """
        try:
            with self._get_cursor() as cursor:
                result = callback(cursor)
                self._get_connection().commit()
                return result
        except mysqlConnector.Error as ex:
            self._rollback(ex)

    def execute_query(self, callback: Callable) -> Any:
        """
        Execute a query callback without transaction commit.

        Args:
            callback: Function that receives a cursor and returns result

        Returns:
            Result from callback, or None on error
        """
        try:
            with self._get_cursor() as cursor:
                return callback(cursor)
        except mysqlConnector.Error as ex:
            error(ex)
            return None

    def execute_and_commit(self, query: str, params: tuple = ()) -> int:
        """Execute a query and commit, returning affected row count."""
        return self.execute_transaction(lambda c: (c.execute(query, params), c.rowcount)[1])

    def execute_all_and_commit(self, queries: list[dict[str, Any]]) -> list[int]:
        """
        Execute multiple queries in a single transaction.

        Args:
            queries: List of dicts with 'query' and optional 'params' keys

        Returns:
            List of row counts for each query
        """
        def op(cursor):
            row_counts = []
            for query in queries:
                cursor.execute(query['query'], query.get('params', ()))
                row_counts.append(cursor.rowcount)
            return row_counts
        return self.execute_transaction(op)

    def _rollback(self, ex: mysqlConnector.Error):
        """Rollback transaction on error."""
        try:
            conn = self._get_connection()
            if conn.is_connected() and conn.in_transaction:
                print(red(f'Rolling back transaction due to error: {ex}'))
                print(yellow(self._fetch_one('SHOW ENGINE INNODB STATUS\\G;')['status']), flush=True)
                conn.rollback()
        except mysqlConnector.Error as rollback_ex:
            print(red(f'Rollback error: {rollback_ex}'))
        raise ex

    def _fetch_one(self, query: str, id: int | str = None) -> dict:
        """Fetch a single row - used for rollback status."""
        return self.execute_query(lambda c: (c.execute(query, [id] if id else []), c.fetchone())[1])

    @contextmanager
    def _get_cursor(self):
        """Get cursor from connection, reconnecting if necessary."""
        conn = self._get_connection()
        if not conn.is_connected():
            print(f'Reconnecting to DB conn: {conn}', flush=True)
            conn.reconnect()
        cursor = conn.cursor()
        cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;')
        try:
            yield cursor
        finally:
            cursor.close()
