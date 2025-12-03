from typing import Dict, Sequence, TypeVar, Union
from contextlib import contextmanager
import mysql.connector as mysqlConnector
from mysql.connector.types import RowItemType

from commonlib.sqlUtil import error, getColumnTranslated

from .decorator.retry import retry
from .terminalColor import green, red, yellow

DEBUG = False

DB_NAME = 'jobs'
QRY_FIND_JOB_BY_JOB_ID = """
SELECT id,jobId FROM jobs WHERE jobId = %s"""
QRY_INSERT = """
INSERT INTO jobs (
    jobId,title,company,location,url,markdown,easy_apply,web_page)
          values (%s,%s,%s,%s,%s,%s,%s,%s)"""

QRY_SELECT_JOBS_VIEWER = """
SELECT {selectFields}
FROM jobs
WHERE {where}
ORDER BY {order}"""
QRY_SELECT_COUNT_JOBS = """
SELECT count(*)
FROM jobs
"""
SELECT_APPLIED_JOB_IDS_BY_COMPANY = """select id, created from jobs
 where applied and lower(company) rlike '{company}' and id != {id} """
SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT = " and client like '%{client}%' "
SELECT_APPLIED_JOB_ORDER_BY = """
order by created desc"""

DB_FIELDS_BOOL = """flagged,`like`,ignored,seen,applied,discarded,closed,
interview_rh,interview,interview_tech,interview_technical_test,interview_technical_test_done,
ai_enriched,easy_apply"""

conn: mysqlConnector.MySQLConnection = None


def getConnection() -> mysqlConnector.MySQLConnection:
    global conn
    if conn is None:
        conn = mysqlConnector.connect(
            user='root', password='rootPass', database='jobs',
            pool_name='jobsPool',
            pool_size=20,
            # connection_timeout=10,
            # get_warnings=True
        )
    if DEBUG:
        print(conn.__repr__())
    # When using pooling, we want to return a connection from the pool,
    # not the pool object itself (which is what conn holds if we used mysqlConnector.pooling.MySQLConnectionPool directly,
    # but here mysqlConnector.connect with pool_name returns a pooled connection?
    # Actually, mysql.connector.connect(pool_name=...) returns a CMySQLConnection or MySQLConnection
    # that is part of a pool.
    # However, if we assign it to a global `conn`, we are holding onto one connection forever.
    # We need to change this pattern.
    
    # If pool_name is specified, connect() returns a connection from the pool.
    # But we want to get a NEW connection from the pool every time getConnection is called,
    # or at least when we are starting a new unit of work.
    
    # The current implementation uses a global `conn` variable.
    # If we enable pooling, we should probably change how we get connections.
    
    # Let's use mysql.connector.pooling explicitly or just rely on connect() returning a pooled connection
    # IF we don't cache it globally.
    
    # But the existing code caches `conn` globally:
    # if conn is None: conn = ...
    
    # If we want to use pooling correctly, we should NOT cache the connection globally
    # if we want multiple threads to get different connections.
    
    # However, to minimize changes and risk, let's look at how to get a connection from the pool.
    # If we use pool_name, subsequent calls to connect with the same pool_name return connections from the pool.
    
    return mysqlConnector.connect(pool_name='jobsPool')


class MysqlUtil:

    def __init__(self, connection=None):
        self.conn = connection if connection else None
        # https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.close()
            self.conn = None

    @contextmanager
    def cursor(self):
        should_close = False
        if not self.conn:
            self.conn = getConnection()
            should_close = True
            
        conn = self.conn
            
        if not conn.is_connected():
            print(f'Reconnecting to DB conn: {conn}', flush=True)
            conn.reconnect()
            
        c = conn.cursor()
        c.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;')
        try:
            yield c
        except Exception:
            raise
        finally:
            c.close()
            if should_close:
                conn.close()
                self.conn = None

    def insert(self, params) -> int | None:
        try:
            with self.cursor() as c:
                c.execute(QRY_INSERT, params)
                self.getConnection().commit()
            return c.lastrowid
        except mysqlConnector.Error as ex:
            error(ex, end='')
            try:
                self.rollback(ex)
            except mysqlConnector.Error as rollbackEx:
                print(red(f'Rollback error: {rollbackEx}'))
            return None
    
    def jobExists(self, job_id: str) -> bool:
        """Check if job exists in database by job_id"""
        existing = self.fetchOne(QRY_FIND_JOB_BY_JOB_ID, job_id)
        return existing is not None
    
    def insertJob(self, job_data) -> int | None:
        """Insert job data and return row ID if successful, None on error"""
        params = (
            job_data.get('job_id', ''),
            job_data.get('title', ''),
            job_data.get('company', ''),
            job_data.get('location', ''),
            job_data.get('url', ''),
            job_data.get('markdown', ''),
            job_data.get('easy_apply', False),
            job_data.get('web_page', '')
        )
        return self.insert(params)

    T = TypeVar("T")  # T = TypeVar("T", bound="List")

    def count(self, query: str, params: Union[Sequence[T], Dict[str, T]] = ()):
        try:
            with self.cursor() as c:
                c.execute(query, params)
                return c.fetchone()[0]
        except mysqlConnector.Error as ex:
            error(ex)

    def fetchOne(self, query: str, id: int | str) -> Dict[str, RowItemType]:
        try:
            with self.cursor() as c:
                c.execute(query, [id])
                return c.fetchone()
        except mysqlConnector.Error as ex:
            error(ex)

    def rollback(self, ex: mysqlConnector.Error):
        # 1205 Lock wait timeout exceeded
        conn = self.getConnection()
        if conn.is_connected() and conn.in_transaction:
            print(red(f'Rolling back transaction due to error: {ex}'))
            print(yellow(self.fetchOne('SHOW ENGINE INNODB STATUS\\G;')['status']), flush=True)
            conn.rollback()
        raise ex

    @retry(retries=5, delay=1, exception=mysqlConnector.Error)
    def updateFromAI(self, query, params):
        try:
            with self.cursor() as c:
                c.execute(query, params)
                self.getConnection().commit()
                if c.rowcount > 0:
                    print(green(f'Updated database: {params}'), flush=True)
                else:
                    error(Exception('No rows affected'))
        except mysqlConnector.Error as ex:
            self.rollback(ex)

    def executeAndCommit(self, query, params=()) -> int:
        try:
            with self.cursor() as c:
                c.execute(query, params)
                self.getConnection().commit()
                return c.rowcount
        except mysqlConnector.Error as ex:
            self.rollback(ex)

    def executeAllAndCommit(self, queries: list[dict[str, any]]) -> int:
        rowCount = []
        try:
            with self.cursor() as c:
                for query in queries:
                    c.execute(query['query'], query.get('params', ()))
                    rowCount.append(c.rowcount)
                self.getConnection().commit()
                return rowCount
        except mysqlConnector.Error as ex:
            self.rollback(ex)

    def fetchAll(self, query: str, params=None):
        with self.cursor() as c:
            c.execute(query, params)
            return c.fetchall()
    
    def getConnection(self):
        """Get the MySQL connection"""
        return self.conn if self.conn else getConnection()

    def getTableDdlColumnNames(self, table):
        """Returns table DDL column names in same order than
          select * from table"""
        columns = self.fetchAll(f'SHOW COLUMNS FROM `{table}`')
        # get column name (idx=0) and translate
        columns = [c[0] for c in columns]
        columns = [getColumnTranslated(c) for c in columns]
        return columns
