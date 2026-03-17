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
        if not start_date or not end_date:
            query = """
                SELECT dateCreated, source, SUM(total) as total
                FROM (
                    SELECT date(created) as dateCreated, web_page as source, COUNT(*) as total FROM jobs GROUP BY dateCreated, source
                    UNION ALL
                    SELECT date(original_created_at) as dateCreated, platform as source, COUNT(*) as total FROM job_snapshots GROUP BY dateCreated, source
                ) combined
                GROUP BY dateCreated, source
                ORDER BY dateCreated
            """
            params = []
        else:
            query = """
                WITH RECURSIVE date_range AS (
                    SELECT CAST(%s AS DATE) as dateCreated
                    UNION ALL
                    SELECT DATE_ADD(dateCreated, INTERVAL 1 DAY) FROM date_range WHERE dateCreated < CAST(%s AS DATE)
                ),
                job_counts AS (
                    SELECT date(created) as dateCreated, web_page as source, COUNT(*) as total
                    FROM jobs
                    WHERE DATE(created) >= CAST(%s AS DATE) AND DATE(created) <= CAST(%s AS DATE)
                    GROUP BY dateCreated, web_page
                ),
                snapshot_counts AS (
                    SELECT date(original_created_at) as dateCreated, platform as source, COUNT(*) as total
                    FROM job_snapshots
                    WHERE DATE(original_created_at) >= CAST(%s AS DATE) AND DATE(original_created_at) <= CAST(%s AS DATE)
                    GROUP BY dateCreated, platform
                ),
                combined_counts AS (
                    SELECT dateCreated, source, total FROM job_counts
                    UNION ALL
                    SELECT dateCreated, source, total FROM snapshot_counts
                )
                SELECT
                    d.dateCreated,
                    COALESCE(c.source, 'Other') as source,
                    COALESCE(c.total, 0) as total
                FROM date_range d
                LEFT JOIN combined_counts c ON d.dateCreated = c.dateCreated
                ORDER BY d.dateCreated
            """
            params = [start_date, end_date, start_date, end_date, start_date, end_date]
        return self._execute(query, params)

    def get_combined_sources_by_hour_df(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        query, params = self._build_union_query("hour", "HOUR(created)", "HOUR(created), web_page", "source, hour", start_date, end_date)
        return self._execute(query, params)

    def get_combined_sources_by_weekday_df(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        query, params = self._build_union_query("weekday", "DAYOFWEEK(created)", "DAYOFWEEK(created), web_page", "weekday, source", start_date, end_date)
        return self._execute(query, params)