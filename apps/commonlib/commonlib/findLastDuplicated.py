from typing import Optional
from .sql.mysqlUtil import MysqlUtil
from .stringUtil import removeNewLines


def find_last_duplicated(mysql: MysqlUtil, title: str, company: str, url: Optional[str] = None) -> int | None:
    """
    Find the last duplicated job by title+company or by URL (excluding 'Joppy').
    Returns the ID of the last duplicated job or None if not found.
    """
    if not url and (not title or not company or company.lower() == 'joppy'):
        return None

    conditions = ["(title = %s AND company = %s)"]
    params = [title or '', company or '']
    if url:
        conditions.append("(url IS NOT NULL AND url = %s)")
        params.append(url)

    query = f"SELECT id FROM jobs WHERE {' OR '.join(conditions)} ORDER BY created DESC LIMIT 1"
    rows = mysql.fetchAll(query, params)
    if rows:
        return rows[0][0]
    return None
