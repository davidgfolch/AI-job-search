import json
from typing import Any, Dict, List, Optional

from commonlib.observability import get_logger
from commonlib.sql.job_filter_builder import (
    BASE_PENDING_CONDITION,
    BOOLEAN_FILTER_KEYS,
    build_jobs_where_clause,
    parse_job_order,
    strip_ai_enriched,
)

logger = get_logger("commonlib.sql.filter_config_selector")


class FilterConfigSelector:
    """Selects enrichment candidates matching the stored watched filter configurations.

    Only watched configurations are considered, iterated in `ordering ASC`. Jobs
    matching any configuration are returned first, following that order and the
    `order` field of each configuration (falling back to `created desc`). The
    ai_enriched filter is always removed from the configuration, because the
    enrichment worker is what sets it.
    """

    QUERY_CONFIGS = "SELECT id, name, filters FROM filter_configurations WHERE watched = 1 ORDER BY ordering ASC"

    def __init__(self, mysql):
        self.mysql = mysql
        self.job_configs: Dict[int, str] = {}

    def priority_ids(self) -> List[int]:
        self.job_configs = {}
        configs = self._load_configs()
        if not configs:
            logger.info("enrich.selection_source", source="default", reason="no_filter_configurations")
            return []
        logger.info("enrich.selection_source", source="filter_configs", configs=[{"position": position, "id": c["id"], "name": c["name"]} for position, c in enumerate(configs, 1)])
        ids: List[int] = []
        seen = set()
        for position, config in enumerate(configs, 1):
            matched = self._match_ids(config["filters"])
            logger.info("enrich.config_working", position=position, config_id=config["id"], config_name=config["name"], matched=len(matched))
            for job_id in matched:
                if job_id not in seen:
                    seen.add(job_id)
                    ids.append(job_id)
                    self.job_configs[job_id] = config["name"]
        if not ids:
            logger.info("enrich.selection_source", source="default", reason="no_filter_config_matches")
        return ids

    def config_for(self, job_id: int) -> Optional[str]:
        return self.job_configs.get(job_id)

    def _load_configs(self) -> List[Dict[str, Any]]:
        try:
            rows = self.mysql.fetchAll(self.QUERY_CONFIGS)
        except Exception as e:
            logger.warning("enrich.configs_unreadable", error=str(e))
            return []
        return [{"id": row[0], "name": row[1], "filters": strip_ai_enriched(self._parse_filters(row[2]))} for row in (rows or [])]

    def _parse_filters(self, raw: Any) -> Dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}

    def _match_ids(self, filters: Dict[str, Any]) -> List[int]:
        where, params = build_jobs_where_clause(
            search=filters.get('search') or None,
            status=filters.get('status'),
            not_status=filters.get('not_status'),
            days_old=filters.get('days_old') or None,
            salary=filters.get('salary') or None,
            sql_filter=filters.get('sql_filter') or None,
            boolean_filters=self._boolean_filters(filters),
        )
        sort_col, sort_dir = parse_job_order(filters.get('order'))
        clauses = [BASE_PENDING_CONDITION] + where
        query = f"SELECT id FROM jobs WHERE {' AND '.join(clauses)} ORDER BY {sort_col} {sort_dir}, created DESC, id DESC"
        return [row[0] for row in (self.mysql.fetchAll(query, params) or [])]

    def _boolean_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        nested = filters.get('boolean_filters') if isinstance(filters.get('boolean_filters'), dict) else {}
        result = {}
        for key in BOOLEAN_FILTER_KEYS:
            val = filters.get(key)
            if val is None:
                val = nested.get(key)
            if val is not None:
                result[key] = val
        return result
