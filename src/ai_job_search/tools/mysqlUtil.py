import re
from typing import Any, Dict, Sequence, TypeVar, Union
import mysql.connector as mysqlConnector

from ai_job_search.tools.decorator.retry import retry
from ai_job_search.tools.terminalColor import printHR, red, yellow

DB_NAME = 'jobs'
QRY_FIND_JOB_BY_JOB_ID = """
SELECT id,jobId FROM jobs WHERE jobId = %s"""
QRY_INSERT = """
INSERT INTO jobs (
    jobId,title,company,location,url,markdown,easy_apply,web_page)
          values (%s,%s,%s,%s,%s,%s,%s,%s)"""
JOBS_FOR_ENRICHMENT = """
FROM jobs
WHERE (ai_enriched IS NULL OR not ai_enriched) and
not (ignored or discarded or closed)
ORDER BY created desc"""
QRY_COUNT_JOBS_FOR_ENRICHMENT = f"""
SELECT count(id) {JOBS_FOR_ENRICHMENT}"""
QRY_FIND_JOBS_IDS_FOR_ENRICHMENT = f"""
SELECT id {JOBS_FOR_ENRICHMENT}"""
QRY_FIND_JOB_FOR_ENRICHMENT = """
SELECT id, title, markdown, company
FROM jobs
WHERE id=%s and not ai_enriched and not (ignored or discarded or closed)
ORDER BY created desc"""
QRY_UPDATE_JOBS_WITH_AI = """
UPDATE jobs SET
    salary=%s,
    required_technologies=%s,
    optional_technologies=%s,
    ai_enriched=1
WHERE id=%s"""
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
 where applied and lower(company) rlike '{company}' and id != {id}"""
SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT = """ and client like '%{client}%'"""


ERROR_PREFIX = 'MysqlError: '
conn: mysqlConnector.MySQLConnection = None


def getConnection() -> mysqlConnector.MySQLConnection:
    global conn
    if conn is None:
        conn = mysqlConnector.connect(
            user='root', password='rootPass', database='jobs',
            # pool_name='jobsPool',
            pool_size=20,
            # connection_timeout=10,
            # get_warnings=True
        )
        print(conn.__repr__())
    return conn


class MysqlUtil:

    def __init__(self, connection=None):
        self.conn = connection if connection else None
        # https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def cursor(self):
        conn = self.conn if self.conn else getConnection()
        if not conn.is_connected():
            print(f'Reconnecting to DB conn: {conn}')
            conn.reconnect()
        c = conn.cursor()
        c.execute('SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;')
        return c

    def insert(self, params) -> int | None:
        try:
            with self.cursor() as c:
                c.execute(QRY_INSERT, params)
                getConnection().commit()
            return c.lastrowid
        except mysqlConnector.Error as ex:
            self.rollback(ex)
            error(ex, end='')
            return None

    T = TypeVar("T")  # T = TypeVar("T", bound="List")

    def count(self, query: str, params: Union[Sequence[T], Dict[str, T]] = ()):
        try:
            with self.cursor() as c:
                c.execute(query, params)
                return c.fetchone()[0]
        except mysqlConnector.Error as ex:
            error(ex)

    def fetchOne(self, query: str, id: int):
        try:
            with self.cursor() as c:
                c.execute(query, [id])
                return c.fetchone()
        except mysqlConnector.Error as ex:
            error(ex)

    def rollback(self, ex: mysqlConnector.Error):
        # 1205 Lock wait timeout exceeded
        if getConnection().is_connected() and getConnection().in_transaction:
            print(red('Lock wait timeout exceeded, retrying'))
            getConnection().rollback()
        raise ex

    @retry(retries=20, delay=1, exception=mysqlConnector.Error)
    def updateFromAI(self, id, company, paramsDict: dict, deep=0):
        params = maxLen(emptyToNone(
            (paramsDict.get('salary', None),
                # TODO: Change to required_skills, optional_skills
                paramsDict.get(f'required_technologies', None),
                paramsDict.get(f'optional_technologies', None),
                id)),
            # TODO: get mysql DDL metadata varchar sizes
            (200, 1000, 1000, None))
        try:
            with self.cursor() as c:
                c.execute(QRY_UPDATE_JOBS_WITH_AI, params)
                getConnection().commit()
                if c.rowcount > 0:
                    print(yellow(f'Inserted into DB (company={company}): {params}'))
                    printHR(yellow)
                else:
                    error(Exception('No rows affected'))
        except mysqlConnector.Error as ex:
            self.rollback(ex)

    def executeAndCommit(self, query, params=()) -> int:
        try:
            with self.cursor() as c:
                c.execute(query, params)
                getConnection().commit()
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
                getConnection().commit()
                return rowCount
        except mysqlConnector.Error as ex:
            self.rollback(ex)

    def fetchAll(self, query: str, params=None):
        with self.cursor() as c:
            c.execute(query, params)
            return c.fetchall()

    def getTableDdlColumnNames(self, table):
        """Returns table DDL column names in same order than
          select * from table"""
        columns = self.fetchAll(f'SHOW COLUMNS FROM `{table}`')
        # get column name (idx=0) and translate
        columns = [c[0] for c in columns]
        columns = [getColumnTranslated(c) for c in columns]
        return columns


# static methods
def getColumnTranslated(c):
    return re.sub(r'`', '', re.sub(r'[_-]', ' ', c)).capitalize()


def updateFieldsQuery(ids: list, fieldsValues: dict, merged=False):
    if len(ids) < 1:
        return
    query = 'UPDATE jobs SET '
    for field in fieldsValues.keys():
        query += f'{field}=%({field})s,'
    if merged:
        query += 'merged=NOW(),'
    query = query[:len(query)-1] + '\n'
    query += 'WHERE id ' + inFilter(ids)
    return query, fieldsValues


def deleteJobsQuery(ids: list[str]):
    if len(ids) < 1:
        return
    query = 'DELETE FROM jobs '
    query += 'WHERE id ' + inFilter(ids)
    return query


def error(ex, suffix='', end='\n'):
    print(red(f'{ERROR_PREFIX}{ex}{suffix}'), end=end)


def emptyToNone(params: tuple[Any]):
    return tuple(
        map(lambda p:
            None if isinstance(p, str) and p.strip() == '' else p,
            params))


def toBoolean(params: tuple[Any]):
    return tuple(
        map(lambda p: bool(p), params))


def maxLen(params: tuple[Any], maxLens: tuple[int]):
    def mapParam(p: tuple):
        val = p[0]
        max = p[1]
        if max is not None and isinstance(val, str) and len(val) > max:
            return val[:max-3]+'...'
        return val
    return tuple(
        map(lambda p: mapParam(p), zip(params, maxLens, strict=True)))


def inFilter(ids: list[int]):
    idsFilter = ','.join([str(id) for id in ids])
    return f' in ({idsFilter})'


def binaryColumnIgnoreCase(col: str) -> str:
    if col in ['comments', 'markdown']:
        return f'CONVERT({col} USING utf8mb4) COLLATE utf8mb4_0900_ai_ci'
    return col
