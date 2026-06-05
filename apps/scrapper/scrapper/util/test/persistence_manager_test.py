import pytest
from unittest.mock import MagicMock
from scrapper.util.persistence_manager import PersistenceManager


class TestPersistenceManager:
    """Tests PersistenceManager with a mock repository (DB mode)."""

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

    def test_update_state_with_repo(self, manager, mock_repo):
        manager.update_state("Site", "new_kw", 5)
        assert mock_repo.upsert.called
        assert manager.state["Site"]["keyword"] == "new_kw"
        assert manager.state["Site"]["page"] == 5
