import pytest
from commonlib.sql import filter_config_selector
from commonlib.sql.filter_config_selector import FilterConfigSelector


class FakeMysql:
    def __init__(self, configs=(), batches=(), raise_on_configs=False):
        self.configs = list(configs)
        self.batches = list(batches)
        self.raise_on_configs = raise_on_configs
        self.calls = []

    def fetchAll(self, query, params=None):
        self.calls.append((query, params))
        if "filter_configurations" in query:
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


def _match_queries(mysql):
    return [q for q, _ in mysql.calls if "filter_configurations" not in q]


def test_iter_batches_without_configs_yields_nothing():
    mysql = FakeMysql()
    assert list(FilterConfigSelector(mysql).iter_batches()) == []
    assert len(_match_queries(mysql)) == 0


def test_iter_batches_returns_nothing_on_config_read_failure():
    mysql = FakeMysql(raise_on_configs=True)
    assert list(FilterConfigSelector(mysql).iter_batches()) == []


def test_iter_batches_follows_config_order_and_chunks():
    mysql = FakeMysql(
        configs=[(1, "Python", '{"search": "python"}'), (2, "Java", '{"search": "java"}')],
        batches=[[(5,), (1,)], [], [(1,), (7,)], []],
    )
    batches = list(FilterConfigSelector(mysql).iter_batches())
    assert batches == [("Python", [5, 1]), ("Java", [1, 7])]


def test_configs_query_only_watched_ordered_by_ordering_asc():
    mysql = FakeMysql()
    list(FilterConfigSelector(mysql).iter_batches())
    config_query = next(q for q, _ in mysql.calls if "filter_configurations" in q)
    assert config_query.endswith("WHERE watched = 1 ORDER BY ordering ASC")


def test_iter_batches_maps_jobs_to_first_matching_config():
    mysql = FakeMysql(
        configs=[(1, "Python", '{}'), (2, "Java", '{}')],
        batches=[[(5,), (1,)], [], [(1,), (7,)], []],
    )
    selector = FilterConfigSelector(mysql)
    list(selector.iter_batches())
    assert selector.config_for(5) == "Python"
    assert selector.config_for(1) == "Python"
    assert selector.config_for(7) == "Java"
    assert selector.config_for(99) is None


def test_match_query_keeps_base_pending_condition():
    mysql = FakeMysql()
    FilterConfigSelector(mysql).match_ids({})
    query = _match_queries(mysql)[0]
    assert "ai_enriched IS NULL OR NOT ai_enriched" in query
    assert "ai_enrich_error" in query
    assert "ignored OR discarded OR closed" in query


def test_match_query_omits_limit_for_first_config():
    mysql = FakeMysql(configs=[(1, "A", '{}')], batches=[[(1,)]])
    list(FilterConfigSelector(mysql).iter_batches())
    assert "LIMIT" not in _match_queries(mysql)[0]

def test_match_query_includes_limit_one_for_later_configs():
    mysql = FakeMysql(configs=[(1, "A", '{}'), (2, "B", '{}')], batches=[[], [(1,)], []])
    list(FilterConfigSelector(mysql).iter_batches())
    assert _match_queries(mysql)[1].endswith("LIMIT 1")


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
    mysql = FakeMysql(configs=[(1, "A", config)], batches=[[(1,)]])
    list(FilterConfigSelector(mysql).iter_batches())
    assert expected in _match_queries(mysql)[0]


def test_integration_priority_backtracking_with_new_jobs():
    mysql = FakeMysql(
        configs=[(1, "FC1", '{}'), (2, "FC2", '{}'), (3, "FC3", '{}')],
        batches=[
            [(1,), (2,)],
            [],
            [(3,)],
            [(5,)],
            [],
            [(4,)],
            [],
            [],
            [(6,)],
            [], [], [], [],
        ],
    )
    batches = list(FilterConfigSelector(mysql).iter_batches())
    assert batches == [
        ("FC1", [1, 2]),
        ("FC2", [3]),
        ("FC1", [5]),
        ("FC2", [4]),
        ("FC3", [6]),
    ]


def test_integration_first_fc_limitless_then_one_by_one_others():
    mysql = FakeMysql(
        configs=[(1, "FC1", '{}'), (2, "FC2", '{}')],
        batches=[
            [(10,), (11,), (12,)],
            [],
            [(20,)],
            [], [], [], [],
        ],
    )
    batches = list(FilterConfigSelector(mysql).iter_batches())
    assert batches == [("FC1", [10, 11, 12]), ("FC2", [20])]


def test_match_query_omits_null_filters():
    mysql = FakeMysql(
        configs=[(1, "A", '{"easy_apply": null, "interview": null, "flagged": null, "search": null, "salary": null, "days_old": null, "sql_filter": null, "applied": true}')],
        batches=[[(1,)]],
    )
    list(FilterConfigSelector(mysql).iter_batches())
    query, _ = mysql.calls[-1]
    for null_key in ("easy_apply", "interview", "flagged"):
        assert f"`{null_key}`" not in query
    assert "`applied` = 1" in query


def test_match_query_strips_ai_enriched_and_keeps_other_filters():
    mysql = FakeMysql()
    selector = FilterConfigSelector(mysql)
    selector.match_ids({"ai_enriched": True, "applied": True, "search": "go", "sql_filter": "salary > 0"})
    query, params = mysql.calls[-1]
    assert "`ai_enriched`" not in query
    assert "`applied` = 1" in query
    assert "title LIKE %s" in query
    assert "(salary > 0)" in query
    assert params == ["%go%", "%go%"]


def test_match_query_reads_nested_boolean_filters():
    mysql = FakeMysql()
    FilterConfigSelector(mysql).match_ids({"boolean_filters": {"ai_enriched": True, "seen": False}})
    query = _match_queries(mysql)[0]
    assert "`ai_enriched`" not in query
    assert "`seen` = 0" in query


def test_logs_selection_source_with_configs_before_match_query(monkeypatch):
    logger = FakeLogger()
    monkeypatch.setattr(filter_config_selector, "logger", logger)
    mysql = FakeMysql(configs=[(7, "Backend", "{}")], batches=[[(1,)]])
    list(FilterConfigSelector(mysql).iter_batches())
    event, fields = logger.events[0]
    assert event == "enrich.selection_source"
    assert fields["source"] == "filter_configs"
    assert fields["configs"] == [{"position": 1, "id": 7, "name": "Backend"}]


def test_logs_default_selection_source_without_configs(monkeypatch):
    logger = FakeLogger()
    monkeypatch.setattr(filter_config_selector, "logger", logger)
    list(FilterConfigSelector(FakeMysql()).iter_batches())
    assert logger.events == [("enrich.selection_source", {"source": "default", "reason": "no_filter_configurations"})]


def test_logs_each_config_in_order_with_match_count(monkeypatch):
    logger = FakeLogger()
    monkeypatch.setattr(filter_config_selector, "logger", logger)
    mysql = FakeMysql(configs=[(1, "Python", '{}'), (2, "Java", '{}')], batches=[[(5,)]])
    list(FilterConfigSelector(mysql).iter_batches())
    working = [event for event in logger.events if event[0] == "enrich.config_working"]
    assert [(fields["position"], fields["config_name"], fields["matched"]) for _, fields in working] == [(1, "Python", 1), (2, "Java", 0)]
