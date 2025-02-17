from ai_job_search.viewer.statistics import (
    appliedDiscardedByDateStats, createdByDate,
    createdByHours)


def stats():
    createdByHours.run()
    createdByDate.run()
    appliedDiscardedByDateStats.run()
