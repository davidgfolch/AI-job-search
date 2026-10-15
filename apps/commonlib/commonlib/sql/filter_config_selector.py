import json
from typing import Any, Dict, Iterator, List, Optional, Tuple

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

    Only watched configurations are considered, iterated in `ordering ASC`. Each
    configuration is drained in chunks of `batch_size`: the worker enriches the
    yielded jobs, they stop satisfying the base pending condition, and the next
    query returns the following chunk. Once a configuration yields no more jobs the
    next one is drained. Jobs are attributed to the first configuration that matched
    them (`config_for`). The ai_enriched filter is always removed from a
    configuration, because the enrichment worker is what sets it.
    """

    QUERY_CONFIGS = "SELECT id, name, filters FROM filter_configurations WHERE watched = 1 ORDER BY ordering ASC"

    def __init__(self, mysql):
        self.mysql = mysql
        self.job_configs: Dict[int, str] = {}

    def iter_batches(self) -> Iterator[Tuple[str, List[int]]]:
        """Yield (config_name, job_ids) draining each watched configuration in chunks of batch_size.

        The first watched configuration keeps batch_size; every later one is
        drained one job at a time."""
        self.job_configs.clear()
        configs = self.load_configs()
        if not configs:
            logger.info("enrich.selection_source", source="default", reason="no_filter_configurations")
            return
        logger.info("enrich.selection_source", source="filter_configs", configs=[{"position": position, "id": c["id"], "name": c["name"]} for position, c in enumerate(configs, 1)])
        matched: dict[int, int] = {position: 0 for position in range(1, len(configs) + 1)}
        matched_any = False
        # Drain in priority order, one chunk per pass. Higher-priority configurations
        # are re-scanned before any further chunk, so newly arrived matches for an
        # earlier configuration are processed before later configurations advance.
        while True:
            progressed = False
            for position, config in enumerate(configs, 1):
                effective_batch_size = None if position == 1 else 1
                ids = self.match_ids(config["filters"], limit=effective_batch_size)
                if ids:
                    matched[position] += len(ids)
                    matched_any = True
                    progressed = True
                    for job_id in ids:
                        self.job_configs.setdefault(job_id, config["name"])
                    yield config["name"], ids
                    break
            if not progressed:
                break
        for position, config in enumerate(configs, 1):
            logger.info("enrich.config_working", position=position, config_id=config["id"], config_name=config["name"], matched=matched[position])
        if not matched_any:
            logger.info("enrich.selection_source", source="default", reason="no_filter_config_matches")

    def config_for(self, job_id: int) -> Optional[str]:
        return self.job_configs.get(job_id)

    def load_configs(self) -> List[Dict[str, Any]]:
        try:
            rows = self.mysql.fetchAll(self.QUERY_CONFIGS)
        except Exception as e:
            logger.warning("enrich.configs_unreadable", error=str(e))
            return []
        return [{"id": row[0], "name": row[1], "filters": strip_ai_enriched(self._parse_filters(row[2]))} for row in (rows or [])]

    def match_ids(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[int]:
        filters = strip_ai_enriched(filters)
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
        if limit is not None:
            query += f" LIMIT {int(limit)}"
        return [row[0] for row in (self.mysql.fetchAll(query, params) or [])]

    def _parse_filters(self, raw: Any) -> Dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}

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
