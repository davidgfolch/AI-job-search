from .mysqlUtil import MysqlUtil
from .stringUtil import removeNewLines


def find_last_duplicated(mysql: MysqlUtil, title: str, company: str) -> int | None:
    """
    Find the last duplicated job by title, company (excluding 'Joppy').
    Returns the ID of the last duplicated job or None if not found.
    """
    if not title or not company or company.lower() == 'joppy':
        return None

    query = """
        SELECT id
        FROM jobs
        WHERE title = %s AND company = %s
        ORDER BY created DESC
        LIMIT 1
    """
    rows = mysql.fetchAll(query, [title, company])
    if rows:
        return rows[0][0]
    return None
