from typing import List, Dict, Any
from repositories.statistics_repository import StatisticsRepository
from repositories.filter_configurations_repository import FilterConfigurationsRepository
from repositories.jobs_repository import JobsRepository



class StatisticsService:
    def __init__(self, repo: StatisticsRepository = None, filter_repo: FilterConfigurationsRepository = None, jobs_repo: JobsRepository = None):
        self.repo = repo or StatisticsRepository()
        self.filter_repo = filter_repo or FilterConfigurationsRepository()
        self.jobs_repo = jobs_repo or JobsRepository()

    def get_history_stats(self) -> List[Dict[str, Any]]:
        df = self.repo.get_history_stats_df()
        
        # Calculate cumulatives
        df['discarded_cumulative'] = df['discarded'].cumsum()
        df['interview_cumulative'] = df['interview'].cumsum()
        
        # Convert to list of dicts for JSON response
        return df.to_dict(orient='records')

    def get_sources_by_date(self) -> List[Dict[str, Any]]:
        df = self.repo.get_sources_by_date_df()
        return df.to_dict(orient='records')

    def get_sources_by_hour(self) -> List[Dict[str, Any]]:
        df = self.repo.get_sources_by_hour_df()
        return df.to_dict(orient='records')

    def get_sources_by_weekday(self) -> list[dict]:
        df = self.repo.get_sources_by_weekday_df()
        return df.to_dict(orient='records')

    def get_filter_configuration_stats(self) -> List[Dict[str, Any]]:
        configs = self.filter_repo.find_all()
        results = []
        for config in configs:
            # Only include if statistics flag is True (default to True for backward compatibility)
            if not config.get('statistics', True):
                continue

            filters = config.get('filters', {})
            where_clauses, params = self.jobs_repo.build_where(
                search=filters.get('search'),
                status=None,
                not_status=None,
                days_old=None,
                salary=filters.get('salary'),
                sql_filter=filters.get('sql_filter'),
                boolean_filters=None,
                ids=filters.get('ids'),
                created_after=None
            )
            where_str = " AND ".join(where_clauses)
            with self.jobs_repo.get_db() as db:
                count = db.count(f"SELECT COUNT(*) FROM jobs WHERE {where_str}", params)
            results.append({
                'name': config['name'],
                'count': count
            })
        return results
