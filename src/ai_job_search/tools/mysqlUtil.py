import re
from typing import Any
import mysql.connector
from mysql.connector import Error

from ai_job_search.terminalColor import red, yellow

DB_NAME = 'jobs'
QRY_FIND_JOB_BY_ID = """
SELECT * FROM jobs WHERE jobId = %s"""
QRY_INSERT = """
INSERT INTO jobs (jobId,title,company,location,url,markdown,easyApply)
          values (%s,%s,%s,%s,%s,%s,%s)"""
QRY_SELECT_JOBS_FOR_ENRICHMENT = """
SELECT id, title, markdown, company
FROM jobs
WHERE not ai_enriched and not (ignored or discarded or closed)
ORDER BY RAND()"""
QRY_UPDATE_JOBS_WITH_AI = """
UPDATE jobs SET
    salary=%s,
    required_technologies=%s,
    optional_technologies=%s,
    relocation=%s,
    business_sector=%s,
    required_languages=%s,
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
WHERE {where}
"""

ERROR_PREFIX = 'MysqlError: '
REGEX_INCORRECT_VALUE_FOR_COL = re.compile(
    "Incorrect [^ ]+ value: (.+(?=for column))for column '(.+)' at .+")


class MysqlUtil:

    def __init__(self):
        self.conn = mysql.connector.connect(
            user='root', password='rootPass', database='jobs',
            # pool_name='jobsPool',
            # pool_size=3,
        )

    def __exit__(self):
        self.conn.close()

    def cursor(self):
        return self.conn.cursor()

    def insert(self, params) -> bool:
        try:
            with self.cursor() as c:
                c.execute(QRY_INSERT, params)
                self.conn.commit()
            return True
        except Error as ex:
            error(ex, end='')
            return False

    def getJob(self, jobId: int):
        try:
            with self.cursor() as c:
                c.execute(QRY_FIND_JOB_BY_ID, [jobId])
                return c.fetchone()
        except mysql.connector.Error as ex:
            error(ex)

    def getJobsForAiEnrichment(self):
        try:
            with self.cursor() as c:
                c.execute(QRY_SELECT_JOBS_FOR_ENRICHMENT)
                return c.fetchall()
        except mysql.connector.Error as ex:
            error(ex)

    def updateFromAI(self, id, company, paramsDict: dict, deep=0):
        try:
            params = maxLen(emptyToNone(
                (paramsDict['salary'],
                 # TODO: Change to required_skills, optional_skills
                 paramsDict['required_technologies'],
                 paramsDict['optional_technologies'],
                 paramsDict['relocation'],
                 paramsDict['business_sector'],
                 paramsDict['required_languages'],
                 id)),
                # TODO: get mysql DDL varchar sizes
                (200, 1000, 1000, None, 1000, 1000, None))
            with self.cursor() as c:
                c.execute(QRY_UPDATE_JOBS_WITH_AI, params)
                self.conn.commit()
                if c.rowcount > 0:
                    print(
                        yellow(f'Inserted into DB (company={company}): ',
                               f'{params}'))
                    print(yellow('-'*150))
                else:
                    error(Exception('No rows affected'))
        except mysql.connector.Error as ex:
            error(ex, f' -> params = {params}')
            if deep > len(paramsDict.keys):
                return
            failColumn = re.sub(REGEX_INCORRECT_VALUE_FOR_COL, r'\2', str(ex))
            if failColumn:
                print(red(f'Found incorrect value for column {failColumn}, ',
                          'retry with column value None'))
                paramsDict[failColumn] = None
                self.updateFromAI(paramsDict, deep+1)

    def executeAndCommit(self, query, params=()) -> int:
        with self.cursor() as c:
            c.execute(query, params)
            self.conn.commit()
            return c.rowcount

    def fetchAll(self, query: str):
        with self.cursor() as c:
            c.execute(query)
            return c.fetchall()

    def count(self, query: str, params: dict = {'where': '1=1'}):
        qry = query.format(**params)
        with self.cursor() as c:
            c.execute(qry)
            return c.fetchall()[0][0]

    def close(self):
        self.conn.close()


# static methods


def updateFieldsQuery(ids: list, fieldsValues: dict):
    if len(ids) < 1:
        return
    query = 'UPDATE jobs SET '
    for field in fieldsValues.keys():
        query += f'{field}=%({field})s,'
    query = query[:len(query)-1] + '\n'
    query += 'WHERE ' + idsFilter(ids)
    return query, fieldsValues


def deleteJobsQuery(ids: list[str]):
    if len(ids) < 1:
        return
    query = 'DELETE FROM jobs '
    query += 'WHERE ' + idsFilter(ids)
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


def idsFilter(ids: list):
    idsFilter = []
    for id in ids:
        idsFilter.append(f'id={int(id)}')
    return ' or '.join(idsFilter)
