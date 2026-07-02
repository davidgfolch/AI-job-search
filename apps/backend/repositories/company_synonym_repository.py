from typing import List, Dict, Any, Optional
from commonlib.sql.mysqlUtil import MysqlUtil, getConnection


class CompanySynonymRepository:
    def __init__(self, mysql: MysqlUtil = None):
        self._mysql = mysql

    def get_db(self) -> MysqlUtil:
        if self._mysql:
            return self._mysql
        return MysqlUtil(getConnection())

    def list_groups(self) -> List[Dict[str, Any]]:
        with self.get_db() as db:
            rows = db.fetchAll(
                "SELECT id, name, group_id FROM company_synonyms ORDER BY group_id, name"
            )
            groups = {}
            for row in rows:
                gid = row[2]
                if gid not in groups:
                    groups[gid] = {"group_id": gid, "names": []}
                groups[gid]["names"].append(row[1])
            return list(groups.values())

    def find_synonyms(self, name: str) -> List[str]:
        with self.get_db() as db:
            row = db.fetchOne(
                "SELECT group_id FROM company_synonyms WHERE name = %s", name
            )
            if not row:
                return []
            group_id = row[0]
            rows = db.fetchAll(
                "SELECT name FROM company_synonyms WHERE group_id = %s AND name != %s ORDER BY name",
                [group_id, name],
            )
            return [r[0] for r in rows]

    def create_group(self, names: List[str]) -> Optional[int]:
        if not names:
            return None
        with self.get_db() as db:
            row = db.fetchOne("SELECT MAX(group_id) FROM company_synonyms")
            next_gid = (row[0] or 0) + 1
            for n in names:
                db.executeAndCommit(
                    "INSERT IGNORE INTO company_synonyms (name, group_id) VALUES (%s, %s)",
                    [n, next_gid],
                )
            return next_gid

    def add_to_group(self, group_id: int, name: str) -> bool:
        with self.get_db() as db:
            try:
                db.executeAndCommit(
                    "INSERT IGNORE INTO company_synonyms (name, group_id) VALUES (%s, %s)",
                    [name, group_id],
                )
                return True
            except Exception:
                return False

    def remove_name(self, name: str) -> bool:
        with self.get_db() as db:
            row = db.fetchOne(
                "SELECT group_id FROM company_synonyms WHERE name = %s", name
            )
            if not row:
                return False
            group_id = row[0]
            db.executeAndCommit(
                "DELETE FROM company_synonyms WHERE name = %s", name
            )
            remaining = db.fetchOne(
                "SELECT COUNT(*) FROM company_synonyms WHERE group_id = %s", group_id
            )
            if remaining and remaining[0] == 0:
                pass
            return True
