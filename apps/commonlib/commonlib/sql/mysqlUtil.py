"""
MySQL utility module - refactored for SRP compliance.

Main entry point: MysqlUtil class composed of:
- ConnectionManager: DB connection pooling
- TransactionManager: Transaction/rollback handling
- QueryExecutor: Query execution (fetch, count)
- JobRepository: Job-specific operations
"""
from contextlib import contextmanager
from mysql.connector import MySQLConnection

from .connection_manager import get_connection, getConnection
from .transaction_manager import TransactionManager
from .query_executor import QueryExecutor
from .job_repository import JobRepository
from .job_queries import (
    QRY_FIND_JOB_BY_JOB_ID,
    QRY_INSERT,
    QRY_SELECT_JOBS_VIEWER,
    QRY_SELECT_COUNT_JOBS,
    SELECT_APPLIED_JOB_IDS_BY_COMPANY,
    SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT,
    SELECT_APPLIED_JOB_ORDER_BY,
    DB_FIELDS_BOOL,
    QRY_UPDATE_JOB_DIRECT_URL,
)
# Re-export for backward compatibility
from ..sqlUtil import getColumnTranslated


class MysqlUtil:
    """
    MySQL utility class providing database operations.

    Composes specialized managers for connection, transaction, and query handling.
    """

    def __init__(self, connection: MySQLConnection = None):
        self._connection = connection
        self._transaction_manager = TransactionManager(self.getConnection)
        self._query_executor = QueryExecutor(self.getConnection)
        self._job_repository = JobRepository(
            self._transaction_manager.execute_transaction,
            self._transaction_manager.execute_query
        )

    @property
    def conn(self) -> MySQLConnection:
        """Backward compatible property for connection access."""
        return self._connection

    @conn.setter
    def conn(self, value: MySQLConnection):
        """Setter for backward compatibility."""
        self._connection = value
        # Reinitialize dependent managers with new connection
        self._transaction_manager = TransactionManager(self.getConnection)
        self._query_executor = QueryExecutor(self.getConnection)
        self._job_repository = JobRepository(
            self._transaction_manager.execute_transaction,
            self._transaction_manager.execute_query
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._connection:
            self._connection.close()
            self._connection = None

    @contextmanager
    def cursor(self):
        """Get a cursor with automatic connection and cleanup."""
        should_close = False
        if not self._connection:
            self._connection = get_connection()
            should_close = True

        conn = self._connection
        if not conn.is_connected():
            print(f'Reconnecting to DB conn: {conn}', flush=True)
            conn.reconnect()

        cursor = conn.cursor()
        cursor.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;')
        try:
            yield cursor
        finally:
            cursor.close()
            if should_close:
                conn.close()
                self._connection = None

    # Job Repository methods
    def insert(self, params) -> int | None:
        """Insert job record with given params."""
        return self._job_repository.insert(params)

    def jobExists(self, job_id: str) -> bool:
        """Check if job exists by job_id."""
        return self._job_repository.job_exists(job_id)

    def insertJob(self, job_data: dict) -> int | None:
        """Insert job from dict data."""
        return self._job_repository.insert_job(job_data)

    # Query Executor methods
    def count(self, query: str, params: tuple = ()) -> int:
        """Execute COUNT query."""
        return self._query_executor.count(query, params)

    def fetchOne(self, query: str, id: int | str) -> dict:
        """Fetch single row by ID."""
        return self._query_executor.fetch_one(query, id)

    def fetchAll(self, query: str, params: tuple = None) -> list:
        """Fetch all matching rows."""
        return self._query_executor.fetch_all(query, params)

    def updateFromAI(self, query: str, params: tuple) -> None:
        """Execute update with retry logic."""
        self._query_executor.update_from_ai(query, params)

    def getTableDdlColumnNames(self, table: str) -> list[str]:
        """Get table column names."""
        return self._query_executor.get_table_ddl_column_names(table)

    # Transaction Manager methods
    def executeAndCommit(self, query: str, params: tuple = ()) -> int:
        """Execute query and commit."""
        return self._transaction_manager.execute_and_commit(query, params)

    def executeAllAndCommit(self, queries: list[dict[str, any]]) -> list[int]:
        """Execute multiple queries in transaction."""
        return self._transaction_manager.execute_all_and_commit(queries)

    def getConnection(self) -> MySQLConnection:
        """Get the MySQL connection."""
        return self._connection if self._connection else get_connection()
