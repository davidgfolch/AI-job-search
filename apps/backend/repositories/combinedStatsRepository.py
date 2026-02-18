from typing import Optional
import pandas as pd
from commonlib.mysqlUtil import getConnection


class CombinedStatsRepository:
    def get_combined_history_stats_df(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
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
                GROUP BY dateCreated
                UNION ALL
                SELECT
                    CONVERT(snapshot_at, DATE) as dateCreated,
                    SUM(applied) as applied,
                    SUM(discarded) as discarded,
                    SUM(interview + interview_rh + interview_tech + interview_technical_test) as interview
                FROM job_snapshots
                GROUP BY dateCreated
            ) combined
            GROUP BY dateCreated
            ORDER BY dateCreated
        """
        conditions = []
        params = []
        if start_date:
            conditions.append("dateCreated >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("dateCreated <= %s")
            params.append(end_date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx, params=params)
        finally:
            cnx.close()

    def get_combined_sources_by_date_df(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
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
                GROUP BY dateCreated, web_page
                UNION ALL
                SELECT
                    date(snapshot_at) as dateCreated,
                    count(*) as total,
                    web_page as source
                FROM job_snapshots
                GROUP BY dateCreated, web_page
            ) combined
            GROUP BY dateCreated, source
            ORDER BY dateCreated
        """
        conditions = []
        params = []
        if start_date:
            conditions.append("dateCreated >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("dateCreated <= %s")
            params.append(end_date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx, params=params)
        finally:
            cnx.close()

    def get_combined_sources_by_hour_df(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
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
                GROUP BY HOUR(created), web_page
                UNION ALL
                SELECT
                    HOUR(snapshot_at) AS hour,
                    web_page as source,
                    COUNT(*) AS total
                FROM job_snapshots
                GROUP BY HOUR(snapshot_at), web_page
            ) combined
            GROUP BY hour, source
            ORDER BY source, hour
        """
        conditions = []
        params = []
        if start_date:
            conditions.append("hour >= 0")
        if end_date:
            conditions.append("hour <= 23")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx, params=params)
        finally:
            cnx.close()

    def get_combined_sources_by_weekday_df(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
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
                GROUP BY weekday, web_page
                UNION ALL
                SELECT
                    DAYOFWEEK(snapshot_at) AS weekday,
                    web_page AS source,
                    COUNT(*) AS total
                FROM job_snapshots
                GROUP BY weekday, web_page
            ) combined
            GROUP BY weekday, source
            ORDER BY weekday, source
        """
        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx)
        finally:
            cnx.close()
