"""Test doubles shared by the filter_config_selector tests."""

CONFIG_TABLE = "filter_configurations"


class FakeMysql:
    """Returns the queued config rows, then the queued match batches in call order."""

    def __init__(self, configs=(), batches=(), raise_on_configs=False):
        self.configs = list(configs)
        self.batches = list(batches)
        self.raise_on_configs = raise_on_configs
        self.calls = []

    def fetchAll(self, query, params=None):
        self.calls.append((query, params))
        if CONFIG_TABLE in query:
            if self.raise_on_configs:
                raise RuntimeError("db down")
            return self.configs
        return self.batches.pop(0) if self.batches else []


class FakeLogger:
    def __init__(self):
        self.events = []

    def info(self, event, **kwargs):
        self.events.append((event, kwargs))

    def warning(self, event, **kwargs):
        self.events.append((event, kwargs))

    def debug(self, event, **kwargs):
        self.events.append((event, kwargs))


def match_queries(mysql):
    """The job-matching queries issued, i.e. every query except the config lookup."""
    return [query for query, _ in mysql.calls if CONFIG_TABLE not in query]
