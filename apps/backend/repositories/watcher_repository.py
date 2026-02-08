import json
from typing import List, Optional, Dict, Any
from commonlib.mysqlUtil import MysqlUtil, getConnection
from commonlib.terminalColor import red
from repositories.queries.view_generator import generate_config_view_sql

class WatcherRepository:

    def get_db(self):
        return MysqlUtil(getConnection())

    def get_watcher_stats_from_view(self, config_ids: List[int]) -> List[tuple]:
        if not config_ids:
            return []
        results = []
        with self.get_db() as db:
            ids_str = ', '.join(['%s'] * len(config_ids))
            configs = db.fetchAll(f"SELECT id, filters FROM filter_configurations WHERE id IN ({ids_str})", config_ids)
            view_names = []
            for cfg in configs:
                cfgId = cfg[0]
                filters = self._parseJsonFilters(cfgId, cfg[1])
                sql, view_name = generate_config_view_sql(cfgId, filters)
                if self._createView(db, sql, view_name, cfgId):
                    view_names.append(view_name)
            if not view_names:
                return []
            union_query = " UNION ALL ".join([f"SELECT config_id, job_created FROM {vn}" for vn in view_names])
            results = db.fetchAll(union_query)
        return results

    def _parseJsonFilters(self, configId: int, filters_json: str) -> Dict[str, Any]:
        if isinstance(filters_json, str):
            try:
                return json.loads(filters_json)
            except:
                print(red(f"Error parsing filters for config {configId}: {filters_json}"))
                return {}
        return filters_json if isinstance(filters_json, dict) else {}

    def _createView(self, db: MysqlUtil, sql: str, view_name: str, configId: int) -> bool:
        try:
            db.executeAndCommit(sql, []) 
            return True
        except Exception as e:
            print(red(f"Error creating view {view_name} for config {configId}: {e}"))
            return False
