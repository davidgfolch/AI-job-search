import pytest
from unittest.mock import MagicMock, patch
from repositories.company_synonym_repository import CompanySynonymRepository


def test_list_groups():
    repo = CompanySynonymRepository()
    with patch.object(repo, "get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.fetchAll.return_value = [
            (1, "Tech Recruiters SL", 1),
            (2, "TRSL Global", 1),
        ]
        result = repo.list_groups()
        assert len(result) == 1
        assert result[0]["group_id"] == 1
        assert "Tech Recruiters SL" in result[0]["names"]
        assert "TRSL Global" in result[0]["names"]


def test_list_groups_multiple_groups():
    repo = CompanySynonymRepository()
    with patch.object(repo, "get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.fetchAll.return_value = [
            (1, "Alpha", 1),
            (2, "Beta", 1),
            (3, "Gamma", 2),
        ]
        result = repo.list_groups()
        assert len(result) == 2
        assert len(result[0]["names"]) == 2
        assert len(result[1]["names"]) == 1


def test_list_groups_empty():
    repo = CompanySynonymRepository()
    with patch.object(repo, "get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.fetchAll.return_value = []
        result = repo.list_groups()
        assert result == []


def test_find_synonyms():
    repo = CompanySynonymRepository()
    with patch.object(repo, "get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.fetchOne.side_effect = [(1,), [(1, "A"), (2, "B")]]
        mock_db.fetchOne.return_value = (1,)
        mock_db.fetchAll.return_value = [("B",)]
        result = repo.find_synonyms("A")
        assert result == ["B"]


def test_find_synonyms_not_found():
    repo = CompanySynonymRepository()
    with patch.object(repo, "get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.fetchOne.return_value = None
        result = repo.find_synonyms("Unknown")
        assert result == []


def test_create_group():
    repo = CompanySynonymRepository()
    with patch.object(repo, "get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.fetchOne.return_value = (0,)
        result = repo.create_group(["A", "B"])
        assert result == 1


def test_create_group_empty():
    repo = CompanySynonymRepository()
    result = repo.create_group([])
    assert result is None


def test_remove_name():
    repo = CompanySynonymRepository()
    with patch.object(repo, "get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.fetchOne.side_effect = [(1,), (1,)]
        result = repo.remove_name("A")
        assert result is True


def test_remove_name_not_found():
    repo = CompanySynonymRepository()
    with patch.object(repo, "get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.fetchOne.return_value = None
        result = repo.remove_name("Unknown")
        assert result is False
