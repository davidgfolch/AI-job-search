import mysql
from commonlib.observability import get_logger

logger = get_logger("backend.repositories.queries.repository_utils")


def execute_with_error_handler(db, where_str: str, params: list, callback, include_items: bool = False, page: int = 0, size: int = 0, order: str = ""):
    try:
        return callback()
    except mysql.connector.errors.DatabaseError as e:
        error_msg = str(e)
        is_syntax = "syntax" in error_msg.lower() or "where" in error_msg.lower()
        if is_syntax:
            human_msg = f"Invalid SQL filter: check your WHERE clause for syntax errors. Error: {error_msg}"
        else:
            human_msg = f"Database error: {error_msg}"
        error_detail = f"{human_msg}\nSQL: {where_str}\nParams: {params}"
        logger.exception("db.query_failed", error=type(e).__name__, syntax_error=is_syntax, include_items=include_items)
        if include_items:
            return {"items": [], "total": 0, "error": error_detail}
        return 0
