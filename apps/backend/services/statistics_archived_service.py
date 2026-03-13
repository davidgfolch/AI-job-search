from typing import List, Dict, Any, Optional
from repositories.snapshots_repository import SnapshotsRepository
from repositories.statistics_repository import StatisticsRepository
from repositories.combinedStatsRepository import CombinedStatsRepository


class StatisticsArchivedService:
    def __init__(
        self,
        snapshots_repo: SnapshotsRepository = None,
        stats_repo: StatisticsRepository = None,
        combined_repo: CombinedStatsRepository = None,
    ):
        self.snapshots_repo = snapshots_repo or SnapshotsRepository()
        self.stats_repo = stats_repo or StatisticsRepository()
        self.combined_repo = combined_repo or CombinedStatsRepository()

    def get_archived_history_stats(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        df = self.snapshots_repo.get_history_stats_df(
            start_date=start_date, end_date=end_date
        )
        if df.empty:
            return []
        return df.to_dict(orient="records")

    def get_archived_sources_by_date(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        df = self.snapshots_repo.get_sources_by_date_df(
            start_date=start_date, end_date=end_date
        )
        return df.to_dict(orient="records")

    def get_archived_sources_by_hour(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        df = self.snapshots_repo.get_sources_by_hour_df(
            start_date=start_date, end_date=end_date
        )
        return df.to_dict(orient="records")

    def get_archived_sources_by_weekday(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        df = self.snapshots_repo.get_sources_by_weekday_df(
            start_date=start_date, end_date=end_date
        )
        return df.to_dict(orient="records")

    def get_combined_history_stats(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        df = self.combined_repo.get_combined_history_stats_df(
            start_date=start_date, end_date=end_date
        )
        if df.empty:
            return []
        df["discarded_cumulative"] = df["discarded"].cumsum()
        df["interview_cumulative"] = df["interview"].cumsum()
        return df.to_dict(orient="records")

    def get_combined_sources_by_date(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        df = self.combined_repo.get_combined_sources_by_date_df(
            start_date=start_date, end_date=end_date
        )
        return df.to_dict(orient="records")

    def get_combined_sources_by_hour(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        df = self.combined_repo.get_combined_sources_by_hour_df(
            start_date=start_date, end_date=end_date
        )
        return df.to_dict(orient="records")

    def get_combined_sources_by_weekday(
        self, start_date: str = None, end_date: str = None
    ) -> List[Dict[str, Any]]:
        df = self.combined_repo.get_combined_sources_by_weekday_df(
            start_date=start_date, end_date=end_date
        )
        return df.to_dict(orient="records")

    def get_snapshots_by_reason(self) -> List[Dict[str, Any]]:
        df = self.snapshots_repo.get_snapshot_count_by_reason()
        return df.to_dict(orient="records")

    def get_snapshots_by_platform(self) -> List[Dict[str, Any]]:
        df = self.snapshots_repo.get_snapshot_count_by_platform()
        return df.to_dict(orient="records")
