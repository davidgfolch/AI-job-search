import hashlib
import json
import os
import threading
from typing import List, Optional, Dict, Any
from commonlib.observability import get_logger
from commonlib.sql.mysqlUtil import MysqlUtil, getConnection
from repositories.queries.view_generator import generate_config_view_sql

logger = get_logger("backend.repositories.watcher_repository")

_VIEW_SIGNATURES: dict[int, str] = {}
_VIEW_SIGNATURE_LOCK = threading.Lock()
_VIEW_DDL_SKIP_ENABLED = os.getenv("PYTEST_CURRENT_TEST") is None and os.getenv("WATCHER_VIEW_DDL_SKIP", "true").lower() not in ("false", "0", "no")


def invalidate_watcher_view(config_id: int) -> None:
    """Forget a cached view signature so the next poll rebuilds it."""
    with _VIEW_SIGNATURE_LOCK:
        _VIEW_SIGNATURES.pop(config_id, None)


def _filter_signature(filters: Any) -> str:
    try:
        payload = json.dumps(filters if filters is not None else {}, sort_keys=True, default=str)
    except (TypeError, ValueError):
        payload = repr(filters)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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
                signature = _filter_signature(filters)
                view_name = f"config_view_{cfgId}"
                skip_ddl = False
                if _VIEW_DDL_SKIP_ENABLED:
                    with _VIEW_SIGNATURE_LOCK:
                        skip_ddl = _VIEW_SIGNATURES.get(cfgId) == signature
                if skip_ddl:
                    view_names.append(view_name)
                    continue

                sql, view_name = generate_config_view_sql(cfgId, filters)
                if self._createView(db, sql, view_name, cfgId):
                    view_names.append(view_name)
                    if _VIEW_DDL_SKIP_ENABLED:
                        with _VIEW_SIGNATURE_LOCK:
                            _VIEW_SIGNATURES[cfgId] = signature
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

    @classmethod
    def invalidate_view(cls, config_id: int) -> None:
        with _VIEW_SIGNATURE_LOCK:
            _VIEW_SIGNATURES.pop(config_id, None)

    @classmethod
    def invalidate_watcher_view(cls, config_id: int) -> None:
        cls.invalidate_view(config_id)
