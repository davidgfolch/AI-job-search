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
WHERE not ai_enriched
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

ERROR_PREFIX = 'MysqlError: '
REGEX_INCORRECT_VALUE_FOR_COL = re.compile(
    "Incorrect [^ ]+ value: (.+(?=for column))for column '(.+)' at .+")


class MysqlUtil:

    def __init__(self):
        self.conn = mysql.connector.connect(
            user='root', password='rootPass',
            database='jobs', pool_name='jobsPool')
        self.cursor = self.conn.cursor()

    def insert(self, params) -> bool:
        try:
            self.cursor.execute(QRY_INSERT, params)
            self.conn.commit()
            return True
        except Error as ex:
            error(ex, end='')
            return False

    def getJob(self, jobId: int):
        try:
            self.cursor.execute(QRY_FIND_JOB_BY_ID, [jobId])
            return self.cursor.fetchone()
        except mysql.connector.Error as ex:
            error(ex)

    def getJobsForAiEnrichment(self):
        try:
            self.cursor.execute(QRY_SELECT_JOBS_FOR_ENRICHMENT)
            return self.cursor.fetchall()
        except mysql.connector.Error as ex:
            error(ex)

    def updateFromAI(self, id, company, paramsDict: dict, deep=0):
        try:
            params = maxLen(emptyToNone(
                (paramsDict['salary'],
                 paramsDict['required_technologies'],
                 paramsDict['optional_technologies'],
                 paramsDict['relocation'],
                 paramsDict['business_sector'],
                 paramsDict['required_languages'],
                 id)),
                (100, 1000, 1000, None, 1000, 1000, None))
            self.cursor.execute(QRY_UPDATE_JOBS_WITH_AI, params)
            self.conn.commit()
            if self.cursor.rowcount > 0:
                print(
                    yellow(f'Inserted into DB (company={company}): {params}'))
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

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


# static methods


def error(ex, suffix='', end='\n'):
    print(red(f'{ERROR_PREFIX}{ex}{suffix}'), end=end)


def emptyToNone(params: tuple[Any]):
    return tuple(
        map(lambda p:
            None if isinstance(p, str) and p.strip() == '' else p,
            params))


def maxLen(params: tuple[Any], maxLens: tuple[int]):
    def mapParam(p: tuple):
        val = p[0]
        max = p[1]
        if max is not None and isinstance(val, str) and len(val) > max:
            return val[:max-3]+'...'
        return val
    return tuple(
        map(lambda p: mapParam(p), zip(params, maxLens, strict=True)))
