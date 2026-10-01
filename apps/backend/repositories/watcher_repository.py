import json
from typing import List, Optional, Dict, Any
from commonlib.observability import get_logger
from commonlib.sql.mysqlUtil import MysqlUtil, getConnection
from repositories.queries.view_generator import generate_config_view_sql

logger = get_logger("backend.repositories.watcher_repository")

class WatcherRepository:

    def get_db(self):
        return MysqlUtil(getConnection())

    def get_watcher_stats_from_view(self, config_ids: List[int]) -> List[tuple]:
        if not config_ids:
            return []
        results = []
        with self.get_db() as db:
            ids_str = ', '.join(['%s'] * len(config_ids))
            configs = db.fetchAll(f"SELECT id, filters FROM filter_configurations WHERE id IN ({ids_str}) AND watched = 1", config_ids)
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
            except Exception as e:
                logger.warning("watcher.filters_parse_failed", error=str(e), config_id=configId)
                return {}
        return filters_json if isinstance(filters_json, dict) else {}

    def _createView(self, db: MysqlUtil, sql: str, view_name: str, configId: int) -> bool:
        try:
            db.executeAndCommit(sql, []) 
            return True
        except Exception as e:
            logger.exception("db.view_creation_failed", error=str(e), view_name=view_name, config_id=configId)
            return False
