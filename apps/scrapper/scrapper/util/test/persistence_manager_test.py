import pytest
from unittest.mock import patch
from scrapper.util.persistence_manager import PersistenceManager

def test_load_from_repository(manager, mock_repo):
    assert manager.state == {"Site": {"keyword": "python"}}
    mock_repo.get_all.assert_called_once()

def test_load_fallback_on_repo_error(mock_repo):
    mock_repo.get_all.side_effect = Exception("DB down")
    pm = PersistenceManager(repository=mock_repo)
    assert pm.state == {}

def test_save_calls_upsert_per_site(manager, mock_repo):
    manager.state = {"A": {"k": "v1"}, "B": {"k": "v2"}}
    manager.save()
    assert mock_repo.upsert.call_count == 2
    mock_repo.upsert.assert_any_call("A", {"k": "v1"})
    mock_repo.upsert.assert_any_call("B", {"k": "v2"})

def test_save_empty_state(mock_repo):
    pm = PersistenceManager(repository=mock_repo)
    pm.state = {}
    pm.save()
    mock_repo.upsert.assert_not_called()

@pytest.mark.parametrize("site,keyword,page", [
    ("Site", "new_kw", 5), ("NewSite", "kw", 1),
], ids=["existing_site", "new_site"])
def test_update_state(site, keyword, page, manager, mock_repo):
    manager.update_state(site, keyword, page)
    assert mock_repo.upsert.called
    assert manager.state[site]["keyword"] == keyword
    assert manager.state[site]["page"] == page

@pytest.mark.parametrize("site,expected", [
    ("Site", {"keyword": "python"}), ("Missing", {}),
], ids=["existing_site", "missing_site"])
def test_get_state(site, expected, manager):
    assert manager.get_state(site) == expected

@pytest.mark.parametrize("site,state", [
    ("Site", {"keyword": "python", "page": 3, "last_execution": "2024-01-01"}),
    ("Missing", {}),
], ids=["existing_site", "missing_site"])
def test_clear_state(site, state, manager, mock_repo):
    manager.state = state
    manager.clear_state(site)
    if site in manager.state:
        assert "keyword" not in manager.state[site]
        assert "page" not in manager.state[site]
        assert manager.state[site]["last_execution"] == "2024-01-01"
        mock_repo.upsert.assert_called()

@pytest.mark.parametrize("site,expected", [
    ("Site", "2024-01-01"), ("Missing", None),
], ids=["existing_site", "missing_site"])
def test_get_last_execution(site, expected, manager):
    if expected is not None:
        manager.state[site]["last_execution"] = expected
    assert manager.get_last_execution(site) == expected

@pytest.mark.parametrize("site", ["Site", "NewSite"], ids=["existing_site", "new_site"])
def test_update_last_execution(site, manager, mock_repo):
    result = manager.update_last_execution(site, "2024-06-01")
    assert result == "2024-06-01"
    assert manager.state[site]["last_execution"] == "2024-06-01"
    mock_repo.upsert.assert_called()

@pytest.mark.parametrize("site,expected", [
    ("NewSite", "2024-06-01 10:00:00"), ("Site", "2024-06-01 12:00:00"),
], ids=["new_site", "existing_site"])
def test_update_last_ran_at(site, expected, manager, mock_repo):
    with patch('scrapper.util.persistence_manager.getDatetimeNowStr', return_value=expected):
        manager.update_last_ran_at(site)
        assert manager.state[site]["last_ran_at"] == expected
        mock_repo.upsert.assert_called()

@pytest.mark.parametrize("last_ran_at,now,parsed,expected", [
    (None, None, None, True),
    ("2024-06-01T10:00:00", 1000000, 999999, False),
    ("2020-01-01T00:00:00", 2000000, 1000000, True),
], ids=["no_last_ran_at", "fresh", "stale"])
def test_is_state_stale(last_ran_at, now, parsed, expected, manager):
    with patch('scrapper.util.persistence_manager.getDatetimeNow', return_value=now):
        with patch('scrapper.util.persistence_manager.parseDatetime', return_value=parsed):
            if last_ran_at:
                manager.state["Site"]["last_ran_at"] = last_ran_at
            assert manager.is_state_stale("Site") is expected

@pytest.mark.parametrize("site,failed,expected", [
    ("Site", [], []), ("Site", ["kw1", "kw2"], ["kw1", "kw2"]), ("Missing", None, []),
], ids=["empty", "with_values", "missing_site"])
def test_get_failed_keywords(site, failed, expected, manager):
    if failed is not None:
        manager.state[site]["failed_keywords"] = failed
    assert manager.get_failed_keywords(site) == expected

@pytest.mark.parametrize("site,initial,keyword,expected,upsert_called", [
    ("Site", None, "failed_kw", ["failed_kw"], True),
    ("Site", ["existing"], "existing", ["existing"], False),
    ("NewSite", None, "kw", ["kw"], True),
], ids=["new_keyword", "duplicate", "new_site"])
def test_add_failed_keyword(site, initial, keyword, expected, upsert_called, manager, mock_repo):
    if initial:
        manager.state[site]["failed_keywords"] = initial
    manager.add_failed_keyword(site, keyword)
    assert manager.state[site]["failed_keywords"] == expected
    assert mock_repo.upsert.called is upsert_called

@pytest.mark.parametrize("site,initial,keyword,expected,upsert_called", [
    ("Site", ["kw1", "kw2"], "kw1", ["kw2"], True),
    ("Site", ["kw1"], "kw2", ["kw1"], False),
    ("Missing", [], "kw", [], False),
], ids=["keyword_exists", "keyword_not_exists", "missing_site"])
def test_remove_failed_keyword(site, initial, keyword, expected, upsert_called, manager, mock_repo):
    if site in manager.state:
        manager.state[site]["failed_keywords"] = initial
    manager.remove_failed_keyword(site, keyword)
    assert manager.get_failed_keywords(site) == expected
    assert mock_repo.upsert.called is upsert_called

@pytest.mark.parametrize("site,state,resume_keyword,resume_page,is_skipping,clears", [
    ("Site", {"keyword": "python", "page": 3, "last_ran_at": "2099-01-01 00:00:00"}, "python", 3, True, False),
    ("Missing", {}, None, 1, False, False),
    ("Site", {"keyword": "python", "page": 3, "last_ran_at": "2020-01-01 00:00:00"}, None, 1, False, True),
    ("Site", {"keyword": "python", "page": 3}, None, 1, False, True),
], ids=["with_state", "no_state", "stale_clears", "no_last_ran_at_clears"])
def test_prepare_resume(site, state, resume_keyword, resume_page, is_skipping, clears, manager, mock_repo):
    manager.state = {site: state}
    manager.prepare_resume(site)
    assert manager._resume_keyword == resume_keyword
    assert manager._resume_page == resume_page
    assert manager._is_skipping is is_skipping
    if clears:
        assert "keyword" not in manager.state[site]
        assert "page" not in manager.state[site]

def test_should_skip_keyword_before_resume(manager):
    manager.state["Site"] = {"keyword": "python", "page": 3, "last_ran_at": "2099-01-01 00:00:00"}
    manager.prepare_resume("Site")
    skip, page = manager.should_skip_keyword("other_kw")
    assert skip is True
    assert page == 1

def test_should_skip_keyword_at_resume_point(manager):
    manager.state["Site"] = {"keyword": "python", "page": 3, "last_ran_at": "2099-01-01 00:00:00"}
    manager.prepare_resume("Site")
    skip, page = manager.should_skip_keyword("python")
    assert skip is False
    assert page == 3
    assert manager._is_skipping is False

def test_should_skip_keyword_after_resume(manager):
    manager.state["Site"] = {"keyword": "python", "page": 3}
    manager.prepare_resume("Site")
    manager.should_skip_keyword("python")
    skip, page = manager.should_skip_keyword("next_kw")
    assert skip is False
    assert page == 1

def test_should_skip_no_resume(manager):
    skip, page = manager.should_skip_keyword("any")
    assert skip is False
    assert page == 1

@pytest.mark.parametrize("site,expected", [
    ("NewSite", "error msg"), ("Site", "new error"),
], ids=["new_site", "existing_site"])
def test_set_error(site, expected, manager, mock_repo):
    with patch('scrapper.util.persistence_manager.getDatetimeNowStr', return_value="2024-01-01T00:00:00"):
        manager.set_error(site, expected)
        assert manager.state[site]["last_error"] == expected
        assert manager.state[site]["last_error_time"] == "2024-01-01T00:00:00"
        mock_repo.upsert.assert_called()

@pytest.mark.parametrize("state,expect_cleared", [
    ({"keyword": "python", "last_error": "err", "last_error_time": "t"}, True),
    ({"failed_keywords": ["kw"], "last_error": "err", "last_error_time": "t"}, False),
    ({"keyword": "python"}, True),
], ids=["clears_errors", "preserves_failed_keywords", "no_errors"])
def test_finalize_scrapper(state, expect_cleared, manager, mock_repo):
    manager.state["Site"] = state
    with patch('scrapper.util.persistence_manager.getDatetimeNowStr'):
        manager.finalize_scrapper("Site")
        assert manager.get_failed_keywords("Site") == state.get("failed_keywords", [])
        if expect_cleared:
            assert "last_error" not in manager.state["Site"]
            assert "last_error_time" not in manager.state["Site"]
            assert "keyword" not in manager.state["Site"]
