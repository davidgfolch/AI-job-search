from typing import Optional
from .sql.mysqlUtil import MysqlUtil
from .stringUtil import removeNewLines


def find_last_duplicated(mysql: MysqlUtil, title: str, company: str, url: Optional[str] = None) -> int | None:
    """
    Find the last duplicated job by title+company or by URL (excluding 'Joppy').
    Returns the ID of the last duplicated job or None if not found.
    """
    conditions = []
    params = []
    if title and company and company.lower() != 'joppy':
        conditions.append("(title = %s AND company = %s)")
        params.extend([title, company])
    if url:
        conditions.append("(url IS NOT NULL AND url = %s)")
        params.append(url)
    if not conditions:
        return None
    query = f"SELECT id FROM jobs WHERE {' OR '.join(conditions)} ORDER BY created DESC LIMIT 1"
    rows = mysql.fetchAll(query, tuple(params))
    if rows:
        return rows[0][0]
    return None
