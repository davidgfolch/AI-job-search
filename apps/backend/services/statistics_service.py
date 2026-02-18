from typing import List, Dict, Any
from repositories.statistics_repository import StatisticsRepository
from repositories.filter_configurations_repository import FilterConfigurationsRepository
from repositories.jobs_repository import JobsRepository


class StatisticsService:
    def __init__(
        self,
        repo: StatisticsRepository = None,
        filter_repo: FilterConfigurationsRepository = None,
        jobs_repo: JobsRepository = None,
    ):
        self.repo = repo or StatisticsRepository()
        self.filter_repo = filter_repo or FilterConfigurationsRepository()
        self.jobs_repo = jobs_repo or JobsRepository()

    def get_history_stats(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        df = self.repo.get_history_stats_df(start_date=start_date, end_date=end_date)

        # Calculate cumulatives
        if not df.empty:
            df["discarded_cumulative"] = df["discarded"].cumsum()
            df["interview_cumulative"] = df["interview"].cumsum()
        else:
            # Handle empty dataframe to avoid errors or return empty list
            return []

        # Convert to list of dicts for JSON response
        return df.to_dict(orient="records")

    def get_sources_by_date(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        df = self.repo.get_sources_by_date_df(start_date=start_date, end_date=end_date)
        return df.to_dict(orient="records")

    def get_sources_by_hour(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        df = self.repo.get_sources_by_hour_df(start_date=start_date, end_date=end_date)
        return df.to_dict(orient="records")

    def get_sources_by_weekday(
        self, start_date: str = None, end_date: str = None
    ) -> list[dict]:
        df = self.repo.get_sources_by_weekday_df(
            start_date=start_date, end_date=end_date
        )
        return df.to_dict(orient="records")

    def get_filter_configuration_stats(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        configs = self.filter_repo.find_all()
        results = []
        with self.jobs_repo.get_db() as db:
            for config in configs:
                # Only include if statistics flag is True (default to True for backward compatibility)
                if not config.get("statistics", True):
                    continue

                filters = config.get("filters", {})
                where_clauses, params = self.jobs_repo.build_where(
                    search=filters.get("search"),
                    status=None,
                    not_status=None,
                    days_old=filters.get("days_old"),
                    salary=filters.get("salary"),
                    sql_filter=filters.get("sql_filter"),
                    boolean_filters=None,
                    ids=filters.get("ids"),
                    created_after=None,
                    start_date=start_date,
                    end_date=end_date,
                )
                where_str = " AND ".join(where_clauses)
                count = self.jobs_repo.count_jobs_query(db, where_str, params)
                results.append({"name": config["name"], "count": count})
        return results
