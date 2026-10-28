PYTHON_CONFIG = (1, '{"search": "python"}')
APPLIED_CONFIG = (2, '{"boolean_filters": {"applied": true}}')


def wire_match(mock_repo, matches_by_config):
    """Make `match_jobs_against_config` return per-config job ids."""
    mock_repo.match_jobs_against_config.side_effect = lambda config_id, where_part, job_ids: matches_by_config.get(config_id, [])


def event_kwargs(mock_logger, level, event):
    """Return the kwargs of every structured record logged under `event` at `level`."""
    calls = getattr(mock_logger, level).call_args_list
    return [c.kwargs for c in calls if c.args and c.args[0] == event]


def event_names(mock_logger, level):
    """Return the event names logged at `level`."""
    return [c.args[0] for c in getattr(mock_logger, level).call_args_list]
