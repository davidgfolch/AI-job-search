import pytest
from commonlib.sql import filter_config_selector
from commonlib.sql.filter_config_selector import FilterConfigSelector


class FakeMysql:
    def __init__(self, configs=(), priority_batches=(), raise_on_configs=False):
        self.configs = list(configs)
        self.priority_batches = list(priority_batches)
        self.raise_on_configs = raise_on_configs
        self.calls = []

    def fetchAll(self, query, params=None):
        self.calls.append((query, params))
        if "filter_configurations" in query:
            if self.raise_on_configs:
                raise RuntimeError("db down")
            return self.configs
        return self.priority_batches.pop(0) if self.priority_batches else []


class FakeLogger:
    def __init__(self):
        self.events = []

    def info(self, event, **kwargs):
        self.events.append((event, kwargs))

    def warning(self, event, **kwargs):
        self.events.append((event, kwargs))

    def debug(self, event, **kwargs):
        self.events.append((event, kwargs))


def _match_queries(mysql):
    return [q for q, _ in mysql.calls if "filter_configurations" not in q]


def test_priority_ids_without_configs_is_empty():
    mysql = FakeMysql()
    assert FilterConfigSelector(mysql).priority_ids() == []
    assert len(_match_queries(mysql)) == 0


def test_priority_ids_returns_empty_on_config_read_failure():
    mysql = FakeMysql(raise_on_configs=True)
    assert FilterConfigSelector(mysql).priority_ids() == []


def test_priority_ids_follows_config_order_and_dedups():
    mysql = FakeMysql(
        configs=[(1, "Python", '{"search": "python"}'), (2, "Java", '{"search": "java"}')],
        priority_batches=[[(5,), (1,)], [(1,), (7,)]],
    )
    assert FilterConfigSelector(mysql).priority_ids() == [5, 1, 7]


def test_configs_query_only_pinned_ordered_by_ordering_asc():
    mysql = FakeMysql()
    FilterConfigSelector(mysql).priority_ids()
    config_query = next(q for q, _ in mysql.calls if "filter_configurations" in q)
    assert config_query.endswith("WHERE pinned = 1 ORDER BY ordering ASC")


def test_priority_ids_maps_jobs_to_first_matching_config():
    mysql = FakeMysql(
        configs=[(1, "Python", '{}'), (2, "Java", '{}')],
        priority_batches=[[(5,), (1,)], [(1,), (7,)]],
    )
    selector = FilterConfigSelector(mysql)
    selector.priority_ids()
    assert selector.config_for(5) == "Python"
    assert selector.config_for(1) == "Python"
    assert selector.config_for(7) == "Java"
    assert selector.config_for(99) is None


def test_match_query_keeps_base_pending_condition():
    mysql = FakeMysql(configs=[(1, "A", '{}')], priority_batches=[[(1,)]])
    FilterConfigSelector(mysql).priority_ids()
    query = _match_queries(mysql)[0]
    assert "ai_enriched IS NULL OR NOT ai_enriched" in query
    assert "ai_enrich_error" in query
    assert "ignored OR discarded OR closed" in query


@pytest.mark.parametrize(
    "config, expected",
    [
        ('{"order": "salary asc"}', "ORDER BY salary asc, created DESC, id DESC"),
        ('{"order": null}', "ORDER BY created desc, created DESC, id DESC"),
        ('{"order": "bogus"}', "ORDER BY created desc, created DESC, id DESC"),
    ],
    ids=["config_order", "null_falls_back_to_created_desc", "invalid_falls_back_to_created_desc"],
)
def test_match_query_ordering(config, expected):
    mysql = FakeMysql(configs=[(1, "A", config)], priority_batches=[[(1,)]])
    FilterConfigSelector(mysql).priority_ids()
    assert expected in _match_queries(mysql)[0]


def test_match_query_omits_null_filters():
    mysql = FakeMysql(
        configs=[(1, "A", '{"easy_apply": null, "interview": null, "flagged": null, "search": null, "salary": null, "days_old": null, "sql_filter": null, "applied": true}')],
        priority_batches=[[(1,)]],
    )
    FilterConfigSelector(mysql).priority_ids()
    query, _ = mysql.calls[-1]
    for null_key in ("easy_apply", "interview", "flagged"):
        assert f"`{null_key}`" not in query
    assert "`applied` = 1" in query


def test_match_query_strips_ai_enriched_and_keeps_other_filters():
    mysql = FakeMysql(
        configs=[(1, "A", '{"ai_enriched": true, "applied": true, "search": "go", "sql_filter": "salary > 0"}')],
        priority_batches=[[(1,)]],
    )
    FilterConfigSelector(mysql).priority_ids()
    query, params = mysql.calls[-1]
    assert "`ai_enriched`" not in query
    assert "`applied` = 1" in query
    assert "title LIKE %s" in query
    assert "(salary > 0)" in query
    assert params == ["%go%", "%go%"]


def test_match_query_reads_nested_boolean_filters():
    mysql = FakeMysql(
        configs=[(1, "A", '{"boolean_filters": {"ai_enriched": true, "seen": false}}')],
        priority_batches=[[(1,)]],
    )
    FilterConfigSelector(mysql).priority_ids()
    query = _match_queries(mysql)[0]
    assert "`ai_enriched`" not in query
    assert "`seen` = 0" in query


def test_logs_selection_source_with_configs_before_match_query(monkeypatch):
    logger = FakeLogger()
    monkeypatch.setattr(filter_config_selector, "logger", logger)
    mysql = FakeMysql(configs=[(7, "Backend", "{}")], priority_batches=[[(1,)]])
    FilterConfigSelector(mysql).priority_ids()
    event, fields = logger.events[0]
    assert event == "enrich.selection_source"
    assert fields["source"] == "filter_configs"
    assert fields["configs"] == [{"position": 1, "id": 7, "name": "Backend"}]


def test_logs_default_selection_source_without_configs(monkeypatch):
    logger = FakeLogger()
    monkeypatch.setattr(filter_config_selector, "logger", logger)
    FilterConfigSelector(FakeMysql()).priority_ids()
    assert logger.events == [("enrich.selection_source", {"source": "default", "reason": "no_filter_configurations"})]


def test_logs_each_config_in_order_with_match_count(monkeypatch):
    logger = FakeLogger()
    monkeypatch.setattr(filter_config_selector, "logger", logger)
    mysql = FakeMysql(
        configs=[(1, "Python", '{}'), (2, "Java", '{}')],
        priority_batches=[[(5,)], []],
    )
    FilterConfigSelector(mysql).priority_ids()
    working = [event for event in logger.events if event[0] == "enrich.config_working"]
    assert [(fields["position"], fields["config_name"], fields["matched"]) for _, fields in working] == [(1, "Python", 1), (2, "Java", 0)]
