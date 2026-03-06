import os
import mysql.connector as mysqlConnector
from mysql.connector import MySQLConnection

DEBUG = False

_pool_initialized = False


def _init_pool(e2e_tests: bool = False):
    """Initialize the connection pool once."""
    global _pool_initialized
    if _pool_initialized:
        return
    db_host = os.getenv('COMMONLIB_DB_HOST', '127.0.0.1')
    mysqlConnector.connect(
        host=db_host,
        user='root',
        password='rootPass',
        database=None if e2e_tests else 'jobs',
        pool_name='jobsPool',
        pool_size=20,
    )
    _pool_initialized = True


def get_connection(e2e_tests: bool = False) -> MySQLConnection:
    """
    Get a MySQL connection from the pool.
    Caller MUST close the connection to return it to the pool.

    Args:
        e2e_tests: If True, initializes pool without database (for E2E test setup)

    Returns:
        MySQL connection instance from pool
    """
    _init_pool(e2e_tests)
    conn = mysqlConnector.connect(pool_name='jobsPool')
    if DEBUG:
        print(conn.__repr__())
    return conn


def getConnection(e2eTests: bool = False) -> MySQLConnection:
    """Backward compatible wrapper for get_connection."""
    return get_connection(e2e_tests=e2eTests)
