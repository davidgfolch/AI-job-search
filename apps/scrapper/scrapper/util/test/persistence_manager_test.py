import pytest
from unittest.mock import MagicMock, patch
from scrapper.util.persistence_manager import PersistenceManager


class TestPersistenceManager:
    @pytest.fixture
    def mock_repo(self):
        repo = MagicMock()
        repo.get_all.return_value = {"Site": {"keyword": "python"}}
        return repo

    @pytest.fixture
    def manager(self, mock_repo):
        return PersistenceManager(repository=mock_repo)

    def test_load_from_repository(self, manager, mock_repo):
        assert manager.state == {"Site": {"keyword": "python"}}
        mock_repo.get_all.assert_called_once()

    def test_load_fallback_on_repo_error(self, mock_repo):
        mock_repo.get_all.side_effect = Exception("DB down")
        pm = PersistenceManager(repository=mock_repo)
        assert pm.state == {}

    def test_save_calls_upsert_per_site(self, manager, mock_repo):
        manager.state = {"A": {"k": "v1"}, "B": {"k": "v2"}}
        manager.save()
        assert mock_repo.upsert.call_count == 2
        mock_repo.upsert.assert_any_call("A", {"k": "v1"})
        mock_repo.upsert.assert_any_call("B", {"k": "v2"})

    def test_update_state_existing_site(self, manager, mock_repo):
        manager.update_state("Site", "new_kw", 5)
        assert mock_repo.upsert.called
        assert manager.state["Site"]["keyword"] == "new_kw"
        assert manager.state["Site"]["page"] == 5

    def test_update_state_new_site(self, manager, mock_repo):
        manager.update_state("NewSite", "kw", 1)
        assert manager.state["NewSite"] == {"keyword": "kw", "page": 1}

    def test_get_state_existing_site(self, manager):
        assert manager.get_state("Site") == {"keyword": "python"}

    def test_get_state_missing_site(self, manager):
        assert manager.get_state("Missing") == {}

    def test_clear_state_with_keyword_and_page(self, manager, mock_repo):
        manager.state = {"Site": {"keyword": "python", "page": 3, "last_execution": "2024-01-01"}}
        manager.clear_state("Site")
        assert "keyword" not in manager.state["Site"]
        assert "page" not in manager.state["Site"]
        assert manager.state["Site"]["last_execution"] == "2024-01-01"
        mock_repo.upsert.assert_called()

    def test_clear_state_missing_site(self, manager, mock_repo):
        manager.state = {}
        manager.clear_state("Missing")  # no error

    def test_get_last_execution_exists(self, manager):
        manager.state["Site"]["last_execution"] = "2024-01-01"
        assert manager.get_last_execution("Site") == "2024-01-01"

    def test_get_last_execution_missing(self, manager):
        assert manager.get_last_execution("Missing") is None

    def test_update_last_execution_existing_site(self, manager, mock_repo):
        result = manager.update_last_execution("Site", "2024-06-01")
        assert result == "2024-06-01"
        assert manager.state["Site"]["last_execution"] == "2024-06-01"
        mock_repo.upsert.assert_called()

    def test_update_last_execution_new_site(self, manager, mock_repo):
        result = manager.update_last_execution("NewSite", "2024-06-01")
        assert result == "2024-06-01"
        assert manager.state["NewSite"]["last_execution"] == "2024-06-01"

    def test_get_failed_keywords_empty(self, manager):
        assert manager.get_failed_keywords("Site") == []

    def test_get_failed_keywords_with_values(self, manager):
        manager.state["Site"]["failed_keywords"] = ["kw1", "kw2"]
        assert manager.get_failed_keywords("Site") == ["kw1", "kw2"]

    def test_get_failed_keywords_missing_site(self, manager):
        assert manager.get_failed_keywords("Missing") == []

    def test_add_failed_keyword_new(self, manager, mock_repo):
        manager.add_failed_keyword("Site", "failed_kw")
        assert "failed_kw" in manager.state["Site"]["failed_keywords"]
        mock_repo.upsert.assert_called()

    def test_add_failed_keyword_duplicate(self, manager, mock_repo):
        manager.state["Site"]["failed_keywords"] = ["existing"]
        manager.add_failed_keyword("Site", "existing")
        assert manager.state["Site"]["failed_keywords"] == ["existing"]

    def test_add_failed_keyword_new_site(self, manager, mock_repo):
        manager.add_failed_keyword("NewSite", "kw")
        assert manager.state["NewSite"]["failed_keywords"] == ["kw"]

    def test_remove_failed_keyword_exists(self, manager, mock_repo):
        manager.state["Site"]["failed_keywords"] = ["kw1", "kw2"]
        manager.remove_failed_keyword("Site", "kw1")
        assert manager.state["Site"]["failed_keywords"] == ["kw2"]
        mock_repo.upsert.assert_called()

    def test_remove_failed_keyword_not_exists(self, manager):
        manager.state["Site"]["failed_keywords"] = ["kw1"]
        manager.remove_failed_keyword("Site", "kw2")  # no error
        assert manager.state["Site"]["failed_keywords"] == ["kw1"]

    def test_remove_failed_keyword_missing_site(self, manager):
        manager.state = {}
        manager.remove_failed_keyword("Missing", "kw")  # no error

    def test_prepare_resume_with_state(self, manager):
        manager.state["Site"] = {"keyword": "python", "page": 3}
        manager.prepare_resume("Site")
        assert manager._resume_keyword == "python"
        assert manager._resume_page == 3
        assert manager._is_skipping is True

    def test_prepare_resume_no_state(self, manager):
        manager.prepare_resume("Missing")
        assert manager._resume_keyword is None
        assert manager._resume_page == 1
        assert manager._is_skipping is False

    def test_should_skip_keyword_before_resume(self, manager):
        manager.prepare_resume("Site")
        skip, page = manager.should_skip_keyword("other_kw")
        assert skip is True
        assert page == 1

    def test_should_skip_keyword_at_resume_point(self, manager):
        manager.state["Site"] = {"keyword": "python", "page": 3}
        manager.prepare_resume("Site")
        skip, page = manager.should_skip_keyword("python")
        assert skip is False
        assert page == 3
        assert manager._is_skipping is False

    def test_should_skip_keyword_after_resume(self, manager):
        manager.state["Site"] = {"keyword": "python", "page": 3}
        manager.prepare_resume("Site")
        manager.should_skip_keyword("python")
        skip, page = manager.should_skip_keyword("next_kw")
        assert skip is False
        assert page == 1

    def test_should_skip_no_resume(self, manager):
        skip, page = manager.should_skip_keyword("any")
        assert skip is False
        assert page == 1

    def test_set_error_new_site(self, manager, mock_repo):
        with patch('scrapper.util.persistence_manager.getDatetimeNowStr', return_value="2024-01-01T00:00:00"):
            manager.set_error("NewSite", "error msg")
            assert manager.state["NewSite"]["last_error"] == "error msg"
            assert manager.state["NewSite"]["last_error_time"] == "2024-01-01T00:00:00"
            mock_repo.upsert.assert_called()

    def test_set_error_existing_site(self, manager, mock_repo):
        with patch('scrapper.util.persistence_manager.getDatetimeNowStr', return_value="2024-06-01T00:00:00"):
            manager.set_error("Site", "new error")
            assert manager.state["Site"]["last_error"] == "new error"
            mock_repo.upsert.assert_called()

    def test_finalize_scrapper_clears_errors(self, manager, mock_repo):
        manager.state["Site"] = {"keyword": "python", "last_error": "err", "last_error_time": "t"}
        with patch('scrapper.util.persistence_manager.getDatetimeNowStr'):
            manager.finalize_scrapper("Site")
            assert "last_error" not in manager.state["Site"]
            assert "last_error_time" not in manager.state["Site"]
            assert "keyword" not in manager.state["Site"]

    def test_finalize_scrapper_preserves_failed_keywords(self, manager, mock_repo):
        manager.state["Site"] = {"failed_keywords": ["kw"], "last_error": "err", "last_error_time": "t"}
        with patch('scrapper.util.persistence_manager.getDatetimeNowStr'):
            manager.finalize_scrapper("Site")
            assert manager.state["Site"]["failed_keywords"] == ["kw"]

    def test_finalize_scrapper_no_errors(self, manager, mock_repo):
        manager.state["Site"] = {"keyword": "python"}
        manager.finalize_scrapper("Site")
        assert "keyword" not in manager.state["Site"]

    def test_save_empty_state(self, mock_repo):
        pm = PersistenceManager(repository=mock_repo)
        pm.state = {}
        pm.save()
        mock_repo.upsert.assert_not_called()
