from ai_job_search.viewer.statistics import (
    appliedDiscardedByDateStats, createdByDate,
    createdByHours)
from ai_job_search.viewer.util.stComponents import reloadButton


def stats():
    reloadButton()
    createdByDate.run()
    createdByHours.run()
    appliedDiscardedByDateStats.run()
