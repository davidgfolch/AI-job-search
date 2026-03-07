from typing import Callable, Any
import mysql.connector as mysqlConnector
from mysql.connector import MySQLConnection
from contextlib import contextmanager

from commonlib.sqlUtil import error
from ..terminalColor import red, yellow


class TransactionManager:
    """Handles database transactions including rollback and commit operations."""

    def __init__(self, get_connection_ctx: Callable):
        self._get_connection_ctx = get_connection_ctx

    def execute_transaction(self, callback: Callable) -> Any:
        """
        Execute a callback within a transaction, committing on success or
        rolling back on error — all on the same connection before it's returned to pool.
        """
        with self._get_cursor() as (conn, cursor):
            try:
                result = callback(cursor)
                conn.commit()
                return result
            except mysqlConnector.Error as ex:
                self._rollback(conn, cursor, ex)

    def execute_query(self, callback: Callable) -> Any:
        """Execute a query callback without transaction commit."""
        try:
            with self._get_cursor() as (_, cursor):
                return callback(cursor)
        except mysqlConnector.Error as ex:
            error(ex)
            return None

    def execute_and_commit(self, query: str, params: tuple = ()) -> int:
        """Execute a query and commit, returning affected row count."""
        return self.execute_transaction(lambda c: (c.execute(query, params), c.rowcount)[1])

    def execute_all_and_commit(self, queries: list[dict[str, Any]]) -> list[int]:
        """Execute multiple queries in a single transaction, returning row counts."""
        def op(cursor):
            row_counts = []
            for query in queries:
                cursor.execute(query['query'], query.get('params', ()))
                row_counts.append(cursor.rowcount)
            return row_counts
        return self.execute_transaction(op)

    def _rollback(self, conn: MySQLConnection, cursor, ex: mysqlConnector.Error):
        """Rollback on the given connection and re-raise."""
        try:
            if conn.in_transaction:
                print(red(f'Rolling back transaction due to error: {ex}'))
                cursor.execute('SHOW ENGINE INNODB STATUS\\G;')
                print(yellow(str(cursor.fetchone())), flush=True)
                conn.rollback()
        except mysqlConnector.Error as rollback_ex:
            print(red(f'Rollback error: {rollback_ex}'))
        raise ex

    @contextmanager
    def _get_cursor(self):
        """Get cursor from pool connection context."""
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
