import json
from typing import List, Optional, Dict, Any
from commonlib.mysqlUtil import MysqlUtil, getConnection

class FilterConfigurationsRepository:
    def get_db(self):
        return MysqlUtil(getConnection())
    
    def find_all(self) -> List[Dict[str, Any]]:
        query = "SELECT * FROM filter_configurations ORDER BY created"
        with self.get_db() as db:
            rows = db.fetchAll(query)
            if not rows:
                return []
            columns = ['id', 'name', 'filters', 'notify', 'created', 'modified']
            result = []
            for row in rows:
                item = {col: val for col, val in zip(columns, row)}
                if item['filters']:
                    item['filters'] = json.loads(item['filters'])
                result.append(item)
            return result
    
    def find_by_id(self, config_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM filter_configurations WHERE id = %s"
        with self.get_db() as db:
            row = db.fetchOne(query, config_id)
            if not row:
                return None
            columns = ['id', 'name', 'filters', 'notify', 'created', 'modified']
            item = {col: val for col, val in zip(columns, row)}
            if item['filters']:
                item['filters'] = json.loads(item['filters'])
            return item
    
    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM filter_configurations WHERE name = %s"
        with self.get_db() as db:
            row = db.fetchOne(query, name)
            if not row:
                return None
            columns = ['id', 'name', 'filters', 'notify', 'created', 'modified']
            item = {col: val for col, val in zip(columns, row)}
            if item['filters']:
                item['filters'] = json.loads(item['filters'])
            return item
    
    def create(self, name: str, filters: dict, notify: bool = False) -> int:
        filters_json = json.dumps(filters)
        query = "INSERT INTO filter_configurations (name, filters, notify) VALUES (%s, %s, %s)"
        with self.get_db() as db:
            db.executeAndCommit(query, [name, filters_json, notify])
            return db.fetchOne("SELECT LAST_INSERT_ID()")[0]
    
    def update(self, config_id: int, name: Optional[str] = None, filters: Optional[dict] = None, notify: Optional[bool] = None) -> bool:
        updates = []
        params = []
        if name is not None:
            updates.append("name = %s")
            params.append(name)
        if filters is not None:
            updates.append("filters = %s")
            params.append(json.dumps(filters))
        if notify is not None:
            updates.append("notify = %s")
            params.append(notify)
        if not updates:
            return True
        params.append(config_id)
        query = f"UPDATE filter_configurations SET {', '.join(updates)} WHERE id = %s"
        with self.get_db() as db:
            db.executeAndCommit(query, params)
            return True
    
    def delete(self, config_id: int) -> bool:
        query = "DELETE FROM filter_configurations WHERE id = %s"
        with self.get_db() as db:
            db.executeAndCommit(query, [config_id])
            return True
    
    def count(self) -> int:
        query = "SELECT COUNT(*) FROM filter_configurations"
        with self.get_db() as db:
            return db.count(query)
