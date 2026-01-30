from typing import Dict, Sequence, TypeVar, Union
from contextlib import contextmanager
import mysql.connector as mysqlConnector
from mysql.connector.types import RowItemType
from commonlib.sqlUtil import error, getColumnTranslated, scapeRegexChars, avoidInjection
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
 where applied and lower(company) rlike '(^|[^a-z0-9]){company}($|[^a-z0-9])' and id != {id} """
SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT = " and client like '%{client}%' "
SELECT_APPLIED_JOB_ORDER_BY = """
order by created desc"""

DB_FIELDS_BOOL = """flagged,`like`,ignored,seen,applied,discarded,closed,
interview_rh,interview,interview_tech,interview_technical_test,interview_technical_test_done,
ai_enriched,easy_apply"""

QRY_UPDATE_JOB_DIRECT_URL = """UPDATE jobs 
                   SET title=%s, company=%s, location=%s, url=%s, markdown=%s, easy_apply=%s 
                   WHERE jobId=%s and web_page=%s"""

conn: mysqlConnector.MySQLConnection = None


def getConnection() -> mysqlConnector.MySQLConnection:
    import os
    global conn
    if conn is None:
        db_host = os.getenv('DB_HOST', '127.0.0.1')  # Docker: mysql_db, Local: 127.0.0.1
        conn = mysqlConnector.connect(
            host=db_host,
            user='root', password='rootPass', database='jobs',
            pool_name='jobsPool',
            pool_size=20,
            # connection_timeout=10,
            # get_warnings=True
        )
    if DEBUG:
        print(conn.__repr__())
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

    def _transaction(self, callback):
        try:
            with self.cursor() as c:
                result = callback(c)
                self.getConnection().commit()
                return result
        except mysqlConnector.Error as ex:
            self.rollback(ex)

    def _query(self, callback):
        try:
            with self.cursor() as c:
                return callback(c)
        except mysqlConnector.Error as ex:
            error(ex)
            return None

    def insert(self, params) -> int | None:
        try:
            return self._transaction(lambda c: (c.execute(QRY_INSERT, params), c.lastrowid)[1])
        except mysqlConnector.Error as ex:
            error(ex, end='')
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
        return self._query(lambda c: (c.execute(query, params), c.fetchone()[0])[1])

    def fetchOne(self, query: str, id: int | str) -> Dict[str, RowItemType]:
        return self._query(lambda c: (c.execute(query, [id]), c.fetchone())[1])

    def rollback(self, ex: mysqlConnector.Error):
        # 1205 Lock wait timeout exceeded
        try:
            conn = self.getConnection()
            if conn.is_connected() and conn.in_transaction:
                print(red(f'Rolling back transaction due to error: {ex}'))
                print(yellow(self.fetchOne('SHOW ENGINE INNODB STATUS\\G;')['status']), flush=True)
                conn.rollback()
        except mysqlConnector.Error as rollbackEx:
            print(red(f'Rollback error: {rollbackEx}'))
        raise ex

    @retry(retries=5, delay=1, exception=mysqlConnector.Error)
    def updateFromAI(self, query, params):
        def op(c):
            c.execute(query, params)
            if c.rowcount > 0:
                print(green(f'Updated database: {params}'), flush=True)
            else:
                error(Exception('No rows affected'))
        self._transaction(op)

    def executeAndCommit(self, query, params=()) -> int:
        return self._transaction(lambda c: (c.execute(query, params), c.rowcount)[1])

    def executeAllAndCommit(self, queries: list[dict[str, any]]) -> int:
        def op(c):
            rowCount = []
            for query in queries:
                c.execute(query['query'], query.get('params', ()))
                rowCount.append(c.rowcount)
            return rowCount
        return self._transaction(op)

    def fetchAll(self, query: str, params=None):
        return self._query(lambda c: (c.execute(query, params), c.fetchall())[1])
    
    def getConnection(self):
        """Get the MySQL connection"""
        return self.conn if self.conn else getConnection()

    def getTableDdlColumnNames(self, table):
        """Returns table DDL column names in same order than select * from table"""
        columns = self.fetchAll(f'SHOW COLUMNS FROM `{table}`')
        # get column name (idx=0) and translate
        columns = [c[0] for c in columns]
        columns = [getColumnTranslated(c) for c in columns]
        return columns
