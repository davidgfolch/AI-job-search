from typing import Optional
import pandas as pd
from commonlib.sql.mysqlUtil import getConnection


class CombinedStatsRepository:
    def _build_date_conditions(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> tuple[list, list]:
        conditions, params = [], []
        if start_date:
            conditions.append("created >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("created <= %s")
            params.append(end_date)
        return conditions, params

    def _build_snapshot_date_conditions(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> tuple[list, list]:
        conditions, params = [], []
        if start_date:
            conditions.append("original_created_at >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("original_created_at <= %s")
            params.append(end_date)
        return conditions, params

    def _execute(self, query: str, params: list) -> pd.DataFrame:
        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx, params=params)
        finally:
            cnx.close()

    def _build_union_query(self, dimension: str, source_expr: str, group_by: str, order_by: str,
                          start_date: Optional[str] = None, end_date: Optional[str] = None) -> tuple[str, list]:
        jobs_cond, jobs_params = self._build_date_conditions(start_date, end_date)
        snaps_cond, snaps_params = self._build_snapshot_date_conditions(start_date, end_date)
        where_jobs = f" WHERE {' AND '.join(jobs_cond)}" if jobs_cond else ""
        where_snaps = f" WHERE {' AND '.join(snaps_cond)}" if snaps_cond else ""

        query = f"""
            SELECT {dimension}, source, SUM(total) as total
            FROM (
                SELECT {source_expr} as {dimension}, web_page as source, COUNT(*) as total FROM jobs{where_jobs} GROUP BY {group_by}, web_page
                UNION ALL
                SELECT {source_expr.replace('created', 'original_created_at').replace('web_page', 'platform')} as {dimension}, platform as source, COUNT(*) as total FROM job_snapshots{where_snaps} GROUP BY {group_by.replace('created', 'original_created_at').replace('web_page', 'platform')}, platform
            ) combined
            GROUP BY {dimension}, source
            ORDER BY {order_by}
        """
        return query, jobs_params + snaps_params

    def get_combined_history_stats_df(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        jobs_cond, jobs_params = self._build_date_conditions(start_date, end_date)
        snaps_cond, snaps_params = self._build_snapshot_date_conditions(start_date, end_date)
        where_jobs = f" WHERE {' AND '.join(jobs_cond)}" if jobs_cond else ""
        where_snaps = f" WHERE {' AND '.join(snaps_cond)}" if snaps_cond else ""

        query = f"""
            SELECT dateCreated, SUM(applied) as applied, SUM(discarded) as discarded, SUM(interview) as interview
            FROM (
                SELECT CONVERT(created, DATE) as dateCreated, SUM(applied) as applied, SUM(discarded) as discarded, SUM(interview + interview_rh + interview_tech + interview_technical_test) as interview FROM jobs{where_jobs} GROUP BY dateCreated
                UNION ALL
                SELECT CONVERT(original_created_at, DATE) as dateCreated, SUM(applied) as applied, SUM(discarded) as discarded, SUM(interview + interview_rh + interview_tech + interview_technical_test) as interview FROM job_snapshots{where_snaps} GROUP BY dateCreated
            ) combined
            GROUP BY dateCreated
            ORDER BY dateCreated
        """
        return self._execute(query, jobs_params + snaps_params)

    def get_combined_sources_by_date_df(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        query, params = self._build_union_query("dateCreated", "date(created)", "dateCreated", "dateCreated", start_date, end_date)
        return self._execute(query, params)

    def get_combined_sources_by_hour_df(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        query, params = self._build_union_query("hour", "HOUR(created)", "HOUR(created), web_page", "source, hour", start_date, end_date)
        return self._execute(query, params)

    def get_combined_sources_by_weekday_df(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        query, params = self._build_union_query("weekday", "DAYOFWEEK(created)", "DAYOFWEEK(created), web_page", "weekday, source", start_date, end_date)
        return self._execute(query, params)