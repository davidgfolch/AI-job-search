import pytest
from unittest.mock import patch, MagicMock
from services.skills_service import SkillsService
from models.skill import Skill

@patch('services.skills_service.SkillsRepository')
def test_list_skills(mock_repo_class):
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_skills = [Skill(name="Python", description="Language", disabled=False)]
    mock_repo.list_skills.return_value = mock_skills
    service = SkillsService()
    result = service.list_skills()
    assert result == mock_skills
    mock_repo.list_skills.assert_called_once()

@patch('services.skills_service.SkillsRepository')
def test_create_skill(mock_repo_class):
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.find_by_name_case_insensitive.return_value = None
    mock_repo.create_skill.return_value = "Python"
    service = SkillsService()
    skill = Skill(name="python", description="Language", disabled=False)
    result = service.create_skill(skill)
    assert result == "Python"
    assert skill.name == "Python"
    mock_repo.find_by_name_case_insensitive.assert_called_once_with("Python")
    mock_repo.create_skill.assert_called_once_with(skill)


@patch('services.skills_service.SkillsRepository')
def test_update_skill(mock_repo_class):
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.find_by_name_case_insensitive.return_value = {'name': 'Python'}
    mock_repo.update_skill.return_value = "Python"
    service = SkillsService()
    result = service.update_skill("python", {"description": "Updated"})
    assert result == "Python"
    mock_repo.find_by_name_case_insensitive.assert_called_once_with("Python")
    mock_repo.update_skill.assert_called_once_with("Python", {"description": "Updated"})

@patch('services.skills_service.SkillsRepository')
def test_delete_skill(mock_repo_class):
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.find_by_name_case_insensitive.return_value = {'name': 'Python'}
    mock_repo.delete_skill.return_value = True
    service = SkillsService()
    result = service.delete_skill("python")
    assert result is True
    mock_repo.find_by_name_case_insensitive.assert_called_once_with("Python")
    mock_repo.delete_skill.assert_called_once_with("Python")


@patch('services.skills_service.SkillsRepository')
def test_bulk_create_skills(mock_repo_class):
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.update_skill.return_value = None
    service = SkillsService()
    skills = [
        Skill(name="Python", description="Lang1", disabled=False),
        Skill(name="Java", description="Lang2", disabled=False)
    ]
    result = service.bulk_create_skills(skills)
    assert result == 2
    assert mock_repo.create_skill.call_count == 2
