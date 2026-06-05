"""Tests for scrapper_state_repository module."""
import json
import pytest
from unittest.mock import MagicMock
from commonlib.sql.scrapper_state_repository import ScrapperStateRepository


class TestScrapperStateRepository:

    @pytest.fixture
    def mock_execute_transaction(self):
        return MagicMock()

    @pytest.fixture
    def mock_execute_query(self):
        return MagicMock()

    @pytest.fixture
    def repo(self, mock_execute_transaction, mock_execute_query):
        return ScrapperStateRepository(mock_execute_transaction, mock_execute_query)

    def test_init(self, mock_execute_transaction, mock_execute_query):
        r = ScrapperStateRepository(mock_execute_transaction, mock_execute_query)
        assert r._execute_transaction == mock_execute_transaction
        assert r._execute_query == mock_execute_query

    def test_get_all_returns_sites_dict(self, repo, mock_execute_query):
        state_json = json.dumps({"keyword": "python", "page": 1})
        mock_execute_query.return_value = [("Linkedin", state_json), ("Infojobs", json.dumps({"keyword": "java"}))]
        result = repo.get_all()
        assert result == {"Linkedin": {"keyword": "python", "page": 1}, "Infojobs": {"keyword": "java"}}

    def test_get_all_returns_empty_on_no_rows(self, repo, mock_execute_query):
        mock_execute_query.return_value = []
        assert repo.get_all() == {}

    @pytest.mark.parametrize("site,state", [
        ("Linkedin", {"keyword": "python", "page": 2}),
        ("Infojobs", {}),
    ], ids=["populated_state", "empty_state"])
    def test_upsert_calls_execute_transaction(self, repo, mock_execute_transaction, site, state):
        repo.upsert(site, state)
        assert mock_execute_transaction.called

    def test_delete_calls_execute_transaction(self, repo, mock_execute_transaction):
        repo.delete("Linkedin")
        assert mock_execute_transaction.called

    def test_replace_all_deletes_and_inserts(self, repo, mock_execute_transaction):
        def fake_transaction(callback):
            fake_cursor = MagicMock()
            callback(fake_cursor)
        mock_execute_transaction.side_effect = fake_transaction

        state = {"Linkedin": {"k": "v"}, "Infojobs": {"k2": "v2"}}
        repo.replace_all(state)
        assert mock_execute_transaction.called
