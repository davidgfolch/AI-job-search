from typing import Optional
import pandas as pd
from commonlib.sql.mysqlUtil import getConnection


class CombinedStatsRepository:
    def _build_date_conditions(self, start_date: str = None, end_date: str = None) -> tuple[list, list]:
        conditions = []
        params = []
        if start_date:
            conditions.append("created >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("created <= %s")
            params.append(end_date)
        return conditions, params

    def _build_snapshot_date_conditions(self, start_date: str = None, end_date: str = None) -> tuple[list, list]:
        conditions = []
        params = []
        if start_date:
            conditions.append("original_created_at >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("original_created_at <= %s")
            params.append(end_date)
        return conditions, params

    def _append_where(self, query: str, conditions: list, params: list) -> tuple[str, list]:
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
            match = __import__('re').search(r"\s+GROUP\s+BY\s+", query, re.IGNORECASE)
            if match:
                start_idx = match.start()
                query = query[:start_idx] + where_clause + query[start_idx:]
        return query, params

    def get_combined_history_stats_df(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        jobs_conditions, jobs_params = self._build_date_conditions(start_date, end_date)
        snapshots_conditions, snapshots_params = self._build_snapshot_date_conditions(start_date, end_date)

        query = """
            SELECT
                dateCreated,
                SUM(applied) as applied,
                SUM(discarded) as discarded,
                SUM(interview) as interview
            FROM (
                SELECT
                    CONVERT(created, DATE) as dateCreated,
                    SUM(applied) as applied,
                    SUM(discarded) as discarded,
                    SUM(interview + interview_rh + interview_tech + interview_technical_test) as interview
                FROM jobs
        """

        if jobs_conditions:
            query += " WHERE " + " AND ".join(jobs_conditions)

        query += """
                GROUP BY dateCreated
                UNION ALL
                SELECT
                    CONVERT(original_created_at, DATE) as dateCreated,
                    SUM(applied) as applied,
                    SUM(discarded) as discarded,
                    SUM(interview + interview_rh + interview_tech + interview_technical_test) as interview
                FROM job_snapshots
        """

        if snapshots_conditions:
            query += " WHERE " + " AND ".join(snapshots_conditions)

        query += """
                GROUP BY dateCreated
            ) combined
            GROUP BY dateCreated
            ORDER BY dateCreated
        """

        params = jobs_params + snapshots_params
        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx, params=params)
        finally:
            cnx.close()

    def get_combined_sources_by_date_df(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        jobs_conditions, jobs_params = self._build_date_conditions(start_date, end_date)
        snapshots_conditions, snapshots_params = self._build_snapshot_date_conditions(start_date, end_date)

        query = """
            SELECT
                dateCreated,
                SUM(total) as total,
                source
            FROM (
                SELECT
                    date(created) as dateCreated,
                    count(*) as total,
                    web_page as source
                FROM jobs
        """

        if jobs_conditions:
            query += " WHERE " + " AND ".join(jobs_conditions)

        query += """
                GROUP BY dateCreated, web_page
                UNION ALL
                SELECT
                    date(original_created_at) as dateCreated,
                    count(*) as total,
                    platform as source
                FROM job_snapshots
        """

        if snapshots_conditions:
            query += " WHERE " + " AND ".join(snapshots_conditions)

        query += """
                GROUP BY dateCreated, platform
            ) combined
            GROUP BY dateCreated, source
            ORDER BY dateCreated
        """

        params = jobs_params + snapshots_params
        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx, params=params)
        finally:
            cnx.close()

    def get_combined_sources_by_hour_df(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        jobs_conditions, jobs_params = self._build_date_conditions(start_date, end_date)
        snapshots_conditions, snapshots_params = self._build_snapshot_date_conditions(start_date, end_date)

        query = """
            SELECT
                hour,
                source,
                SUM(total) as total
            FROM (
                SELECT
                    HOUR(created) AS hour,
                    web_page as source,
                    COUNT(*) AS total
                FROM jobs
        """

        if jobs_conditions:
            query += " WHERE " + " AND ".join(jobs_conditions)

        query += """
                GROUP BY HOUR(created), web_page
                UNION ALL
                SELECT
                    HOUR(original_created_at) AS hour,
                    platform as source,
                    COUNT(*) AS total
                FROM job_snapshots
        """

        if snapshots_conditions:
            query += " WHERE " + " AND ".join(snapshots_conditions)

        query += """
                GROUP BY HOUR(original_created_at), platform
            ) combined
            GROUP BY hour, source
            ORDER BY source, hour
        """

        params = jobs_params + snapshots_params
        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx, params=params)
        finally:
            cnx.close()

    def get_combined_sources_by_weekday_df(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        jobs_conditions, jobs_params = self._build_date_conditions(start_date, end_date)
        snapshots_conditions, snapshots_params = self._build_snapshot_date_conditions(start_date, end_date)

        query = """
            SELECT
                weekday,
                source,
                SUM(total) as total
            FROM (
                SELECT
                    DAYOFWEEK(created) AS weekday,
                    web_page AS source,
                    COUNT(*) AS total
                FROM jobs
        """

        if jobs_conditions:
            query += " WHERE " + " AND ".join(jobs_conditions)

        query += """
                GROUP BY weekday, web_page
                UNION ALL
                SELECT
                    DAYOFWEEK(original_created_at) AS weekday,
                    platform AS source,
                    COUNT(*) AS total
                FROM job_snapshots
        """

        if snapshots_conditions:
            query += " WHERE " + " AND ".join(snapshots_conditions)

        query += """
                GROUP BY weekday, platform
            ) combined
            GROUP BY weekday, source
            ORDER BY weekday, source
        """

        params = jobs_params + snapshots_params
        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx, params=params)
        finally:
            cnx.close()
