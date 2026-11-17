import json
from typing import List

from commonlib.repositories.skill_repository import DESCRIPTION_AND_PATH_UPDATE, DESCRIPTION_UPDATE
from commonlib.skill_context import get_skill_context
from commonlib.sql.mysqlUtil import MysqlUtil

PENDING_ENRICHMENT_QUERY = "SELECT name FROM job_skills WHERE COALESCE(ai_enriched, 0) = 0{description_filter} LIMIT %s"
EMPTY_DESCRIPTION_FILTER = " AND (description IS NULL OR description = '')"
PENDING_LEARNING_PATH_QUERY = (
    "SELECT name FROM job_skills WHERE ai_enriched = 1 "
    "AND (learning_path IS NULL OR JSON_LENGTH(learning_path) = 0) "
    "ORDER BY disabled ASC, name ASC LIMIT %s"
)
UPDATE_LEARNING_PATH_QUERY = (
    "UPDATE job_skills SET learning_path = %s WHERE name = %s "
    "AND (learning_path IS NULL OR JSON_LENGTH(learning_path) = 0)"
)
PENDING_PRIORITY_QUERY = f"SELECT name FROM job_skills WHERE COALESCE(ai_enriched, 0) = 0{EMPTY_DESCRIPTION_FILTER} LIMIT 1"


class SkillRepository:
    """Every `job_skills` read/write performed by aiEnrichSkill.

    Services receive an instance and never touch `MysqlUtil` directly, so the SQL
    (and its guards) lives in one place and the service layer stays DB agnostic.
    """

    def __init__(self, mysql: MysqlUtil):
        self._mysql = mysql

    def fetch_pending_skill_names(self, limit: int, empty_description_only: bool = False) -> List[str]:
        description_filter = EMPTY_DESCRIPTION_FILTER if empty_description_only else ""
        query = PENDING_ENRICHMENT_QUERY.format(description_filter=description_filter)
        return _first_column(self._mysql.fetchAll(query, (limit,)))

    def fetch_pending_learning_path_names(self, limit: int) -> List[str]:
        return _first_column(self._mysql.fetchAll(PENDING_LEARNING_PATH_QUERY, (limit,)))

    def has_pending_enrichment(self) -> bool:
        """Whether tier 1 has work it can actually pick up (the same filter `run_pending_enrichment` uses)."""
        return bool(self._mysql.fetchAll(PENDING_PRIORITY_QUERY))

    def fetch_skill_context(self, name: str) -> str:
        return get_skill_context(self._mysql, name)

    def save_learning_path(self, name: str, learning_path: List[str]) -> None:
        self._mysql.executeAndCommit(UPDATE_LEARNING_PATH_QUERY, [json.dumps(learning_path), name])

    def save_skill_result(self, name: str, description: str, category: str, learning_path: List[str]) -> None:
        if learning_path:
            self._mysql.executeAndCommit(DESCRIPTION_AND_PATH_UPDATE, [description, category, json.dumps(learning_path), name])
        else:
            self._mysql.executeAndCommit(DESCRIPTION_UPDATE, [description, category, name])


def _first_column(rows) -> List[str]:
    return [row[0] for row in (rows or [])]
