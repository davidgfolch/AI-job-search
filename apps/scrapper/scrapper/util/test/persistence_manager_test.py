import pytest
from unittest.mock import patch
from scrapper.util import persistence_manager
from scrapper.util.persistence_manager import PersistenceManager
from scrapper.test.log_capture import captured_records
from scrapper.util.test.persistence_manager_data import (
    LOG_MODULE, UPDATE_STATE, GET_STATE, CLEAR_STATE, GET_LAST_EXECUTION, UPDATE_LAST_EXECUTION,
    UPDATE_LAST_RAN_AT, IS_STATE_STALE, GET_FAILED_KEYWORDS, ADD_FAILED_KEYWORD, REMOVE_FAILED_KEYWORD,
    PREPARE_RESUME, SET_ERROR, FINALIZE,
)

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

@pytest.mark.parametrize("site,keyword,page", UPDATE_STATE)
def test_update_state(site, keyword, page, manager, mock_repo):
    manager.update_state(site, keyword, page)
    assert mock_repo.upsert.called
    assert manager.state[site]["keyword"] == keyword
    assert manager.state[site]["page"] == page

@pytest.mark.parametrize("site,expected", GET_STATE)
def test_get_state(site, expected, manager):
    assert manager.get_state(site) == expected

@pytest.mark.parametrize("site,state", CLEAR_STATE)
def test_clear_state(site, state, manager, mock_repo):
    manager.state = state
    manager.clear_state(site)
    if site in manager.state:
        assert "keyword" not in manager.state[site]
        assert "page" not in manager.state[site]
        assert manager.state[site]["last_execution"] == "2024-01-01"
        mock_repo.upsert.assert_called()

@pytest.mark.parametrize("site,expected", GET_LAST_EXECUTION)
def test_get_last_execution(site, expected, manager):
    if expected is not None:
        manager.state[site]["last_execution"] = expected
    assert manager.get_last_execution(site) == expected

@pytest.mark.parametrize("site", UPDATE_LAST_EXECUTION)
def test_update_last_execution(site, manager, mock_repo):
    result = manager.update_last_execution(site, "2024-06-01")
    assert result == "2024-06-01"
    assert manager.state[site]["last_execution"] == "2024-06-01"
    mock_repo.upsert.assert_called()

@pytest.mark.parametrize("site,expected", UPDATE_LAST_RAN_AT)
def test_update_last_ran_at(site, expected, manager, mock_repo):
    with patch('scrapper.util.persistence_manager.getDatetimeNowStr', return_value=expected):
        manager.update_last_ran_at(site)
        assert manager.state[site]["last_ran_at"] == expected
        mock_repo.upsert.assert_called()

@pytest.mark.parametrize("last_ran_at,now,parsed,expected", IS_STATE_STALE)
def test_is_state_stale(last_ran_at, now, parsed, expected, manager):
    with patch('scrapper.util.persistence_manager.getDatetimeNow', return_value=now):
        with patch('scrapper.util.persistence_manager.parseDatetime', return_value=parsed):
            if last_ran_at:
                manager.state["Site"]["last_ran_at"] = last_ran_at
            assert manager.is_state_stale("Site") is expected

@pytest.mark.parametrize("site,failed,expected", GET_FAILED_KEYWORDS)
def test_get_failed_keywords(site, failed, expected, manager):
    if failed is not None:
        manager.state[site]["failed_keywords"] = failed
    assert manager.get_failed_keywords(site) == expected

@pytest.mark.parametrize("site,initial,keyword,expected,upsert_called", ADD_FAILED_KEYWORD)
def test_add_failed_keyword(site, initial, keyword, expected, upsert_called, manager, mock_repo):
    if initial:
        manager.state[site]["failed_keywords"] = initial
    manager.add_failed_keyword(site, keyword)
    assert manager.state[site]["failed_keywords"] == expected
    assert mock_repo.upsert.called is upsert_called

@pytest.mark.parametrize("site,initial,keyword,expected,upsert_called", REMOVE_FAILED_KEYWORD)
def test_remove_failed_keyword(site, initial, keyword, expected, upsert_called, manager, mock_repo):
    if site in manager.state:
        manager.state[site]["failed_keywords"] = initial
    manager.remove_failed_keyword(site, keyword)
    assert manager.get_failed_keywords(site) == expected
    assert mock_repo.upsert.called is upsert_called

@pytest.mark.parametrize("site,state,resume_keyword,resume_page,is_skipping,clears", PREPARE_RESUME)
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

def test_should_skip_keyword_never_skips_failed_keyword(manager):
    manager.state["Site"] = {"keyword": "python", "page": 3, "last_ran_at": "2099-01-01 00:00:00"}
    manager.prepare_resume("Site")
    manager.add_failed_keyword("Site", "java")
    skip, page = manager.should_skip_keyword("java")
    assert skip is False
    assert page == 1

def test_should_skip_keyword_keeps_skipping_non_failed_before_resume(manager):
    manager.state["Site"] = {"keyword": "python", "page": 3, "last_ran_at": "2099-01-01 00:00:00"}
    manager.prepare_resume("Site")
    manager.add_failed_keyword("Site", "java")
    skip, page = manager.should_skip_keyword("other")
    assert skip is True
    assert page == 1

@pytest.mark.parametrize("site,expected", SET_ERROR)
def test_set_error(site, expected, manager, mock_repo):
    with patch('scrapper.util.persistence_manager.getDatetimeNowStr', return_value="2024-01-01T00:00:00"):
        manager.set_error(site, expected)
        assert manager.state[site]["last_error"] == expected
        assert manager.state[site]["last_error_time"] == "2024-01-01T00:00:00"
        mock_repo.upsert.assert_called()

@pytest.mark.parametrize("state,expect_cleared", FINALIZE)
def test_finalize_scrapper(state, expect_cleared, manager, mock_repo):
    manager.state["Site"] = state
    with patch('scrapper.util.persistence_manager.getDatetimeNowStr'):
        manager.finalize_scrapper("Site")
        assert manager.get_failed_keywords("Site") == state.get("failed_keywords", [])
        if expect_cleared:
            assert "last_error" not in manager.state["Site"]
            assert "last_error_time" not in manager.state["Site"]
            assert "keyword" not in manager.state["Site"]


class TestFinalizeScrapperLogging:
    def test_logs_preserved_state_with_failure_count(self, manager, mock_repo):
        manager.state["Site"] = {"failed_keywords": ["kw1", "kw2"]}
        with captured_records(persistence_manager, LOG_MODULE) as records:
            manager.finalize_scrapper("Site")
        assert [r["event"] for r in records] == ["state.preserved_with_failures"]
        assert records[0]["log_level"] == "warning"
        assert records[0]["site"] == "Site"
        assert records[0]["failed_count"] == 2

    def test_logs_nothing_when_state_is_cleared(self, manager, mock_repo):
        manager.state["Site"] = {"keyword": "python"}
        with captured_records(persistence_manager, LOG_MODULE) as records:
            manager.finalize_scrapper("Site")
        assert records == []
