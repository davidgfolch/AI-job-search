import pytest

LOG_MODULE = "scrapper.persistence_manager"

UPDATE_STATE = [
    pytest.param("Site", "new_kw", 5, id="existing_site"),
    pytest.param("NewSite", "kw", 1, id="new_site"),
]
GET_STATE = [
    pytest.param("Site", {"keyword": "python"}, id="existing_site"),
    pytest.param("Missing", {}, id="missing_site"),
]
CLEAR_STATE = [
    pytest.param("Site", {"keyword": "python", "page": 3, "last_execution": "2024-01-01"}, id="existing_site"),
    pytest.param("Missing", {}, id="missing_site"),
]
GET_LAST_EXECUTION = [
    pytest.param("Site", "2024-01-01", id="existing_site"),
    pytest.param("Missing", None, id="missing_site"),
]
UPDATE_LAST_EXECUTION = [
    pytest.param("Site", id="existing_site"),
    pytest.param("NewSite", id="new_site"),
]
UPDATE_LAST_RAN_AT = [
    pytest.param("NewSite", "2024-06-01 10:00:00", id="new_site"),
    pytest.param("Site", "2024-06-01 12:00:00", id="existing_site"),
]
IS_STATE_STALE = [
    pytest.param(None, None, None, True, id="no_last_ran_at"),
    pytest.param("2024-06-01T10:00:00", 1000000, 999999, False, id="fresh"),
    pytest.param("2020-01-01T00:00:00", 2000000, 1000000, True, id="stale"),
]
GET_FAILED_KEYWORDS = [
    pytest.param("Site", [], [], id="empty"),
    pytest.param("Site", ["kw1", "kw2"], ["kw1", "kw2"], id="with_values"),
    pytest.param("Missing", None, [], id="missing_site"),
]
ADD_FAILED_KEYWORD = [
    pytest.param("Site", None, "failed_kw", ["failed_kw"], True, id="new_keyword"),
    pytest.param("Site", ["existing"], "existing", ["existing"], False, id="duplicate"),
    pytest.param("NewSite", None, "kw", ["kw"], True, id="new_site"),
]
REMOVE_FAILED_KEYWORD = [
    pytest.param("Site", ["kw1", "kw2"], "kw1", ["kw2"], True, id="keyword_exists"),
    pytest.param("Site", ["kw1"], "kw2", ["kw1"], False, id="keyword_not_exists"),
    pytest.param("Missing", [], "kw", [], False, id="missing_site"),
]
PREPARE_RESUME = [
    pytest.param("Site", {"keyword": "python", "page": 3, "last_ran_at": "2099-01-01 00:00:00"}, "python", 3, True, False, id="with_state"),
    pytest.param("Missing", {}, None, 1, False, False, id="no_state"),
    pytest.param("Site", {"keyword": "python", "page": 3, "last_ran_at": "2020-01-01 00:00:00"}, None, 1, False, True, id="stale_clears"),
    pytest.param("Site", {"keyword": "python", "page": 3}, None, 1, False, True, id="no_last_ran_at_clears"),
]
SET_ERROR = [
    pytest.param("NewSite", "error msg", id="new_site"),
    pytest.param("Site", "new error", id="existing_site"),
]
FINALIZE = [
    pytest.param({"keyword": "python", "last_error": "err", "last_error_time": "t"}, True, id="clears_errors"),
    pytest.param({"failed_keywords": ["kw"], "last_error": "err", "last_error_time": "t"}, False, id="preserves_failed_keywords"),
    pytest.param({"keyword": "python"}, True, id="no_errors"),
]
