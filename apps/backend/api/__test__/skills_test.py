import pytest
from unittest.mock import patch
from models.skill import Skill

@patch('services.skills_service.SkillsService.list_skills')
def test_list_skills(mock_list, client):
    mock_skills = [
        Skill(name="Python", description="Programming language", learning_path=["basics", "advanced"], disabled=False),
        Skill(name="JavaScript", description="Web language", learning_path=["js101"], disabled=False)
    ]
    mock_list.return_value = mock_skills
    response = client.get("/api/skills")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["name"] == "Python"

@patch('services.skills_service.SkillsService.create_skill')
def test_create_skill(mock_create, client):
    mock_create.return_value = "Python"
    skill_data = {"name": "Python", "description": "Programming language", "learning_path": ["basics"], "disabled": False}
    response = client.post("/api/skills/Python", json=skill_data)
    assert response.status_code == 200
    assert response.json() == "Python"

@patch('services.skills_service.SkillsService.update_skill')
def test_update_skill(mock_update, client):
    mock_update.return_value = "Python"
    update_data = {"name": "Python", "description": "Updated description"}
    response = client.put("/api/skills/Python", json=update_data)
    assert response.status_code == 200
    assert response.json() == "Python"

@patch('services.skills_service.SkillsService.update_skill')
def test_update_skill_not_found(mock_update, client):
    mock_update.return_value = None
    update_data = {"name": "Unknown", "description": "Test"}
    response = client.put("/api/skills/Unknown", json=update_data)
    assert response.status_code == 404

@patch('services.skills_service.SkillsService.delete_skill')
def test_delete_skill(mock_delete, client):
    mock_delete.return_value = True
    response = client.delete("/api/skills/Python")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@patch('services.skills_service.SkillsService.delete_skill')
def test_delete_skill_not_found(mock_delete, client):
    mock_delete.return_value = False
    response = client.delete("/api/skills/Unknown")
    assert response.status_code == 404
