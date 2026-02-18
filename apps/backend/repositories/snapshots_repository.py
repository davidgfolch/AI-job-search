import pandas as pd
from commonlib.mysqlUtil import getConnection


class SnapshotsRepository:
    def get_history_stats_df(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        query = """
            SELECT
                CONVERT(snapshot_at, DATE) as dateCreated,
                SUM(applied) as applied,
                SUM(discarded) as discarded,
                SUM(interview + interview_rh + interview_tech + interview_technical_test) as interview
            FROM job_snapshots
            GROUP BY dateCreated
            ORDER BY dateCreated
        """
        conditions = []
        params = []
        if start_date:
            conditions.append("snapshot_at >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("snapshot_at <= %s")
            params.append(end_date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx, params=params)
        finally:
            cnx.close()

    def get_sources_by_date_df(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        query = """
            SELECT
                date(snapshot_at) as dateCreated,
                count(*) as total,
                web_page as source
            FROM job_snapshots
            GROUP BY dateCreated, web_page
            ORDER BY dateCreated
        """
        conditions = []
        params = []
        if start_date:
            conditions.append("snapshot_at >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("snapshot_at <= %s")
            params.append(end_date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx, params=params)
        finally:
            cnx.close()

    def get_sources_by_hour_df(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        query = """
            SELECT
                HOUR(snapshot_at) AS hour,
                max(web_page) as source,
                COUNT(*) AS total
            FROM job_snapshots
            GROUP BY HOUR(snapshot_at), web_page
            ORDER BY web_page, hour
        """
        conditions = []
        params = []
        if start_date:
            conditions.append("snapshot_at >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("snapshot_at <= %s")
            params.append(end_date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx, params=params)
        finally:
            cnx.close()

    def get_sources_by_weekday_df(
        self, start_date: str = None, end_date: str = None
    ) -> pd.DataFrame:
        query = """
            SELECT
                DAYOFWEEK(snapshot_at) AS weekday,
                web_page AS source,
                COUNT(*) AS total
            FROM job_snapshots
            GROUP BY weekday, web_page
            ORDER BY weekday, source
        """
        conditions = []
        params = []
        if start_date:
            conditions.append("snapshot_at >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("snapshot_at <= %s")
            params.append(end_date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx, params=params)
        finally:
            cnx.close()

    def get_snapshot_count_by_reason(self) -> pd.DataFrame:
        query = """
            SELECT snapshot_reason, COUNT(*) as count
            FROM job_snapshots
            GROUP BY snapshot_reason
            ORDER BY count DESC
        """
        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx)
        finally:
            cnx.close()

    def get_snapshot_count_by_platform(self) -> pd.DataFrame:
        query = """
            SELECT platform, COUNT(*) as count
            FROM job_snapshots
            GROUP BY platform
            ORDER BY count DESC
        """
        cnx = getConnection()
        try:
            return pd.read_sql(query, cnx)
        finally:
            cnx.close()
