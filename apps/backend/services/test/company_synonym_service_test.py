import pytest
from unittest.mock import MagicMock
from services.company_synonym_service import CompanySynonymService
from repositories.company_synonym_repository import CompanySynonymRepository


@pytest.fixture
def mock_repo():
    return MagicMock(spec=CompanySynonymRepository)


@pytest.fixture
def sut(mock_repo):
    svc = CompanySynonymService()
    svc.repo = mock_repo
    return svc


def test_list_groups(sut, mock_repo):
    mock_repo.list_groups.return_value = [{"group_id": 1, "names": ["A", "B"]}]
    result = sut.list_groups()
    assert len(result) == 1
    mock_repo.list_groups.assert_called_once()


def test_get_synonyms(sut, mock_repo):
    mock_repo.find_synonyms.return_value = ["B", "C"]
    result = sut.get_synonyms("A")
    assert result == ["B", "C"]
    mock_repo.find_synonyms.assert_called_once_with("A")


def test_get_synonyms_not_found(sut, mock_repo):
    mock_repo.find_synonyms.return_value = []
    result = sut.get_synonyms("Unknown")
    assert result == []


def test_create_group(sut, mock_repo):
    mock_repo.create_group.return_value = 1
    result = sut.create_group(["A", "B"])
    assert result == 1
    mock_repo.create_group.assert_called_once_with(["A", "B"])


@pytest.mark.parametrize("names", [
    (["A"],),
    ([],),
], ids=["single_name", "empty_list"])
def test_create_group_invalid(sut, names):
    result = sut.create_group(names)
    assert result is None


def test_add_to_group(sut, mock_repo):
    mock_repo.add_to_group.return_value = True
    result = sut.add_to_group(1, "C")
    assert result is True
    mock_repo.add_to_group.assert_called_once_with(1, "C")


def test_remove_name(sut, mock_repo):
    mock_repo.remove_name.return_value = True
    result = sut.remove_name("A")
    assert result is True
    mock_repo.remove_name.assert_called_once_with("A")


def test_remove_name_not_found(sut, mock_repo):
    mock_repo.remove_name.return_value = False
    result = sut.remove_name("Unknown")
    assert result is False
