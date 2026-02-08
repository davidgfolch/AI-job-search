import json
from typing import List, Optional, Dict, Any
from commonlib.mysqlUtil import MysqlUtil, getConnection
from repositories.queries.view_generator import drop_config_view_sql

class FilterConfigurationsRepository:

    def get_db(self):
        return MysqlUtil(getConnection())
    
    def find_all(self) -> List[Dict[str, Any]]:
        query = "SELECT * FROM filter_configurations ORDER BY created"
        with self.get_db() as db:
            rows = db.fetchAll(query)
            if not rows:
                return []
            columns = ['id', 'name', 'filters', 'notify', 'statistics', 'created', 'modified']
            result = []
            for row in rows:
                if len(row) == 6:
                     pass 
            pass

    def find_all(self) -> List[Dict[str, Any]]:
        query = "SELECT id, name, filters, notify, statistics, pinned, created, modified FROM filter_configurations ORDER BY created"
        with self.get_db() as db:
            rows = db.fetchAll(query)
            if not rows:
                return []
            columns = ['id', 'name', 'filters', 'notify', 'statistics', 'pinned', 'created', 'modified']
            result = []
            for row in rows:
                item = {col: val for col, val in zip(columns, row)}
                if item['filters']:
                    try:
                        item['filters'] = json.loads(item['filters'])
                    except:
                        item['filters'] = {}
                result.append(item)
            return result
    
    def find_by_id(self, config_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT id, name, filters, notify, statistics, pinned, created, modified FROM filter_configurations WHERE id = %s"
        with self.get_db() as db:
            row = db.fetchOne(query, config_id)
            if not row:
                return None
            columns = ['id', 'name', 'filters', 'notify', 'statistics', 'pinned', 'created', 'modified']
            item = {col: val for col, val in zip(columns, row)}
            if item['filters']:
                try:
                    item['filters'] = json.loads(item['filters'])
                except:
                    item['filters'] = {}
            return item
    
    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        query = "SELECT id, name, filters, notify, statistics, pinned, created, modified FROM filter_configurations WHERE name = %s"
        with self.get_db() as db:
            row = db.fetchOne(query, name)
            if not row:
                return None
            columns = ['id', 'name', 'filters', 'notify', 'statistics', 'pinned', 'created', 'modified']
            item = {col: val for col, val in zip(columns, row)}
            if item['filters']:
                try:
                    item['filters'] = json.loads(item['filters'])
                except:
                    item['filters'] = {}
            return item
    
    def create(self, name: str, filters: dict, notify: bool = False, statistics: bool = True, pinned: bool = False) -> int:
        filters_json = json.dumps(filters)
        query = "INSERT INTO filter_configurations (name, filters, notify, statistics, pinned) VALUES (%s, %s, %s, %s, %s)"
        
        def op(c):
            c.execute(query, [name, filters_json, notify, statistics, pinned])
            return c.lastrowid
            
        with self.get_db() as db:
            return db._transaction(op)
    
    def update(self, config_id: int, name: Optional[str] = None, filters: Optional[dict] = None, notify: Optional[bool] = None, statistics: Optional[bool] = None, pinned: Optional[bool] = None) -> bool:
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
        if statistics is not None:
            updates.append("statistics = %s")
            params.append(statistics)
        if pinned is not None:
            updates.append("pinned = %s")
            params.append(pinned)
        if not updates:
            return True
        params.append(config_id)
        query = f"UPDATE filter_configurations SET {', '.join(updates)} WHERE id = %s"
        with self.get_db() as db:
            db.executeAndCommit(query, params)
            return True
    
    def delete(self, config_id: int) -> bool:
        drop_view_sql = drop_config_view_sql(config_id)
        delete_query = "DELETE FROM filter_configurations WHERE id = %s"
        queries = [
            {'query': delete_query, 'params': [config_id]},
            {'query': drop_view_sql}
        ]
        with self.get_db() as db:
            db.executeAllAndCommit(queries)
            return True
    
    def count(self) -> int:
        query = "SELECT COUNT(*) FROM filter_configurations"
        with self.get_db() as db:
            return db.count(query)
