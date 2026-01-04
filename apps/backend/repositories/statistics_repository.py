import pandas as pd
from commonlib.mysqlUtil import getConnection

class StatisticsRepository:
    def get_history_stats_df(self) -> pd.DataFrame:
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
        cnx = getConnection()
        return pd.read_sql(query, cnx)

    def get_sources_by_date_df(self) -> pd.DataFrame:
        query = """
            SELECT
                date(created) as dateCreated,
                count(*) as total,
                web_page as source
            from jobs
            group by dateCreated, web_page
            order by dateCreated
        """
        cnx = getConnection()
        return pd.read_sql(query, cnx)

    def get_sources_by_hour_df(self) -> pd.DataFrame:
        query = """
            SELECT
                HOUR(created) AS hour,
                max(web_page) as source,
                COUNT(*) AS total
            FROM jobs
            GROUP BY HOUR(created), web_page
            order by web_page, hour
        """
        cnx = getConnection()
        return pd.read_sql(query, cnx)
