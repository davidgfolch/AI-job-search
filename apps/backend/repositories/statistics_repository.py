import re
import pandas as pd
from commonlib.mysqlUtil import getConnection

class StatisticsRepository:
    def _apply_date_filter(self, query: str, start_date: str = None, end_date: str = None) -> tuple[str, list]:
        conditions = []
        params = []
        if start_date:
            conditions.append("created >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("created <= %s")
            params.append(end_date)
            
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
            
            # Find GROUP BY case-insensitively
            match = re.search(r"\s+group\s+by\s+", query, re.IGNORECASE)
            if match:
                start_idx = match.start()
                query = query[:start_idx] + where_clause + query[start_idx:]
            else:
                query += where_clause
        
        return query, params

    def get_history_stats_df(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        query = """
            SELECT
                CONVERT(created, DATE) as dateCreated,
                SUM(applied) as applied,
                SUM(discarded) as discarded,
                SUM(interview + interview_rh + interview_tech + interview_technical_test) as interview
            FROM jobs
            GROUP BY dateCreated
            ORDER BY dateCreated
        """
        query, params = self._apply_date_filter(query, start_date, end_date)
        cnx = getConnection()
        return pd.read_sql(query, cnx, params=params)

    def get_sources_by_date_df(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        query = """
            SELECT
                date(created) as dateCreated,
                count(*) as total,
                web_page as source
            from jobs
            group by dateCreated, web_page
            order by dateCreated
        """
        query, params = self._apply_date_filter(query, start_date, end_date)
        cnx = getConnection()
        return pd.read_sql(query, cnx, params=params)

    def get_sources_by_hour_df(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        query = """
            SELECT
                HOUR(created) AS hour,
                max(web_page) as source,
                COUNT(*) AS total
            FROM jobs
            GROUP BY HOUR(created), web_page
            order by web_page, hour
        """
        query, params = self._apply_date_filter(query, start_date, end_date)
        cnx = getConnection()
        return pd.read_sql(query, cnx, params=params)

    def get_sources_by_weekday_df(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        query = """
            SELECT
                DAYOFWEEK(created) AS weekday,
                web_page AS source,
                COUNT(*) AS total
            FROM jobs
            GROUP BY weekday, web_page
            ORDER BY weekday, web_page;
        """
        query, params = self._apply_date_filter(query, start_date, end_date)
        cnx = getConnection()
        return pd.read_sql(query, cnx, params=params)
