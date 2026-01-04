from typing import List, Dict, Any
from repositories.statistics_repository import StatisticsRepository

class StatisticsService:
    def __init__(self, repo: StatisticsRepository = None):
        self.repo = repo or StatisticsRepository()

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
