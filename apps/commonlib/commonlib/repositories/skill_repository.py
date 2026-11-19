from typing import List, Sequence
from commonlib.skill_context import get_skill_context
from commonlib.skill_learning_path import LearningPathLink, serialize_learning_path
from commonlib.sql.mysqlUtil import MysqlUtil

DESCRIPTION_UPDATE = "UPDATE job_skills SET description = %s, category = %s, ai_enriched = 1 WHERE name = %s"
DESCRIPTION_AND_PATH_UPDATE = (
    "UPDATE job_skills SET description = %s, category = %s, ai_enriched = 1, "
    "learning_path = CASE WHEN (learning_path IS NULL OR JSON_LENGTH(learning_path) = 0) "
    "THEN %s ELSE learning_path END WHERE name = %s"
)


class SkillRepository:
    """Every `job_skills` read/write used by the shared skill-enrichment loop."""

    def __init__(self, mysql: MysqlUtil):
        self._mysql = mysql

    def fetch_pending_skill_names(self, limit: int, check_empty_description_only: bool = True) -> List[str]:
        where_clause = "COALESCE(ai_enriched, 0) = 0"
        if check_empty_description_only:
            where_clause += " AND (description IS NULL OR description = '')"
        rows = self._mysql.fetchAll(f"SELECT name FROM job_skills WHERE {where_clause} LIMIT {limit}")
        return [row[0] for row in (rows or [])]

    def fetch_skill_context(self, name: str) -> str:
        return get_skill_context(self._mysql, name)

    def save_skill_result(self, name: str, description: str, category: str, learning_path: Sequence[LearningPathLink | str]) -> None:
        if learning_path:
            self._mysql.executeAndCommit(DESCRIPTION_AND_PATH_UPDATE, [description, category, serialize_learning_path(learning_path), name])
        else:
            self._mysql.executeAndCommit(DESCRIPTION_UPDATE, [description, category, name])
