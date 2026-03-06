"""
SQL queries and constants for job-related database operations.

These constants are used by backend and scrapper modules.
"""

QRY_FIND_JOB_BY_JOB_ID = """
SELECT id,jobId FROM jobs WHERE jobId = %s"""

QRY_INSERT = """
INSERT INTO jobs (
    jobId,title,company,location,url,markdown,easy_apply,web_page,duplicated_id)
          values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

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
