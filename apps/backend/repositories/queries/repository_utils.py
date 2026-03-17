import mysql
from commonlib.terminalColor import red
from commonlib.exceptionUtil import filter_trace_by_paths


def execute_with_error_handler(db, where_str: str, params: list, callback, include_items: bool = False, page: int = 0, size: int = 0, order: str = ""):
    try:
        return callback()
    except mysql.connector.errors.DatabaseError as e:
        filtered = filter_trace_by_paths(["apps/"])
        error_msg = str(e)
        if "syntax" in error_msg.lower() or "where" in error_msg.lower():
            human_msg = f"Invalid SQL filter: check your WHERE clause for syntax errors. Error: {error_msg}"
        else:
            human_msg = f"Database error: {error_msg}"
        error_detail = f"{human_msg}\nSQL: {where_str}\nParams: {params}"
        if filtered:
            error_detail += f"\n{filtered}"
        print(red(error_detail))
        if include_items:
            return {"items": [], "total": 0, "error": error_detail}
        return 0
