from .sql.mysqlUtil import MysqlUtil
from .stringUtil import removeNewLines
from .company_normalizer import is_unspecified_company


def find_last_duplicated(mysql: MysqlUtil, title: str, company: str, exclude_id: int | None = None) -> int | None:
    """
    Find the last duplicated job by title, company (excluding 'Joppy' and unspecified companies).
    Duplicate detection is meaningless while the company is generic, so it is deferred until
    the real company is known (see AiEnrichRepository.refresh_duplicated_of).
    exclude_id skips a job id, needed when the job being checked already exists in DB.
    Returns the ID of the last duplicated job or None if not found.
    """
    if not title or is_unspecified_company(company) or company.lower() == 'joppy':
        return None

    query = """
        SELECT id
        FROM jobs
        WHERE title = %s AND company = %s
    """
    params = [title, company]
    if exclude_id is not None:
        query += " AND id != %s"
        params.append(exclude_id)
    query += """
        ORDER BY created DESC
        LIMIT 1
    """
    rows = mysql.fetchAll(query, params)
    if rows:
        return rows[0][0]
    return None
