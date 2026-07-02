import pytest
from unittest.mock import patch

create_mock_db = pytest.create_mock_db


@patch("repositories.company_synonym_repository.CompanySynonymRepository.get_db")
def test_list_synonym_groups(mock_get_db, client):
    mock_db = create_mock_db(fetchAll=[(1, "A", 1), (2, "B", 1)])
    mock_get_db.return_value = mock_db
    response = client.get("/api/company-synonyms")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["group_id"] == 1
    assert "A" in data[0]["names"]
    assert "B" in data[0]["names"]


@patch("repositories.company_synonym_repository.CompanySynonymRepository.get_db")
def test_list_synonym_groups_empty(mock_get_db, client):
    mock_db = create_mock_db(fetchAll=[])
    mock_get_db.return_value = mock_db
    response = client.get("/api/company-synonyms")
    assert response.status_code == 200
    assert response.json() == []


@patch("repositories.company_synonym_repository.CompanySynonymRepository.get_db")
def test_get_synonyms(mock_get_db, client):
    mock_db = create_mock_db(fetchOne=(1,), fetchAll=[("B",)])
    mock_get_db.return_value = mock_db
    response = client.get("/api/company-synonyms/synonyms?company=A")
    assert response.status_code == 200
    assert response.json() == ["B"]


@patch("repositories.company_synonym_repository.CompanySynonymRepository.get_db")
def test_get_synonyms_not_found(mock_get_db, client):
    mock_db = create_mock_db(fetchOne=None)
    mock_get_db.return_value = mock_db
    response = client.get("/api/company-synonyms/synonyms?company=Unknown")
    assert response.status_code == 200
    assert response.json() == []


@patch("repositories.company_synonym_repository.CompanySynonymRepository.get_db")
def test_create_group(mock_get_db, client):
    mock_db = create_mock_db(fetchOne=(0,))
    mock_get_db.return_value = mock_db
    response = client.post("/api/company-synonyms/groups", json={"names": ["A", "B"]})
    assert response.status_code == 200
    assert response.json()["group_id"] == 1


@pytest.mark.parametrize("names", [
    [],
    ["A"],
], ids=["empty_names", "single_name"])
@patch("repositories.company_synonym_repository.CompanySynonymRepository.get_db")
def test_create_group_invalid(mock_get_db, client, names):
    response = client.post("/api/company-synonyms/groups", json={"names": names})
    assert response.status_code == 400
    assert "two names" in response.json()["detail"].lower()


@patch("repositories.company_synonym_repository.CompanySynonymRepository.get_db")
def test_add_to_group(mock_get_db, client):
    mock_db = create_mock_db()
    mock_get_db.return_value = mock_db
    response = client.post("/api/company-synonyms/groups/1", json={"name": "C"})
    assert response.status_code == 200


@patch("repositories.company_synonym_repository.CompanySynonymRepository.get_db")
def test_remove_name(mock_get_db, client):
    mock_db = create_mock_db(fetchOne=(1,), executeAndCommit=1)
    mock_get_db.return_value = mock_db
    response = client.delete("/api/company-synonyms/names/A")
    assert response.status_code == 200


@patch("repositories.company_synonym_repository.CompanySynonymRepository.get_db")
def test_remove_name_not_found(mock_get_db, client):
    mock_db = create_mock_db(fetchOne=None)
    mock_get_db.return_value = mock_db
    response = client.delete("/api/company-synonyms/names/Unknown")
    assert response.status_code == 404
