from typing import Dict, List, Optional
from .base_repository import BaseRepository
from ..mysqlUtil import MysqlUtil

class Job:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class JobRepository(BaseRepository):
    def __init__(self, mysqlUtil: MysqlUtil):
        self.mysql = mysqlUtil

    def findById(self, id: int) -> Optional[Job]:
        query = "SELECT * FROM jobs WHERE id = %s"
        result = self.mysql.fetchOne(query, id)
        return Job(**dict(zip(self._getColumns(), result))) if result else None

    def findAll(self, filters: Dict[str, any] = None) -> List[Job]:
        query = "SELECT * FROM jobs"
        params = []
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = %s")
                params.append(value)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        results = self.mysql.fetchAll(query, params)
        return [Job(**dict(zip(self._getColumns(), row))) for row in results]

    def save(self, entity: Job) -> Job:
        pass

    def delete(self, id: int) -> bool:
        query = "DELETE FROM jobs WHERE id = %s"
        affected = self.mysql.executeAndCommit(query, [id])
        return affected > 0

    def count(self, filters: Dict[str, any] = None) -> int:
        query = "SELECT COUNT(*) FROM jobs"
        params = []
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = %s")
                params.append(value)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        return self.mysql.count(query, params)

    def _getColumns(self) -> List[str]:
        return self.mysql.getTableDdlColumnNames('jobs')