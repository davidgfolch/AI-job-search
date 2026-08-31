import pytest
from unittest.mock import patch, MagicMock
from repositories.skills_repository import SkillsRepository
from models.skill import Skill
from commonlib.test.db_mock_util import create_mock_db

@patch('repositories.skills_repository.MysqlUtil')
@patch('repositories.skills_repository.getConnection')
def test_list_skills(mock_get_connection, mock_mysql_util):
    mock_db = create_mock_db(fetchAll=[
        ('Python', 'Programming language', '["basics", "advanced"]', 0, 0, 'Language'),
        ('JavaScript', 'Web language', None, 0, 0, 'Language')
    ])
    mock_mysql_util.return_value = mock_db
    repo = SkillsRepository()
    skills = repo.list_skills()
    assert len(skills) == 2
    assert skills[0].name == 'Python'
    assert len(skills[0].learning_path) == 2

@patch('repositories.skills_repository.MysqlUtil')
@patch('repositories.skills_repository.getConnection')
def test_create_skill(mock_get_connection, mock_mysql_util):
    mock_db = create_mock_db()
    mock_mysql_util.return_value = mock_db
    repo = SkillsRepository()
    skill = Skill(name="Python", description="Language", learning_path=["basics"], disabled=False)
    result = repo.create_skill(skill)
    assert result == "Python"
    mock_db.executeAndCommit.assert_called_once()

@patch('repositories.skills_repository.MysqlUtil')
@patch('repositories.skills_repository.getConnection')
def test_update_skill(mock_get_connection, mock_mysql_util):
    mock_db = create_mock_db(fetchOne=('Python',))
    mock_mysql_util.return_value = mock_db
    repo = SkillsRepository()
    result = repo.update_skill('Python', {'description': 'Updated'})
    assert result == 'Python'
    mock_db.executeAndCommit.assert_called_once()

@patch('repositories.skills_repository.MysqlUtil')
@patch('repositories.skills_repository.getConnection')
def test_update_skill_not_found(mock_get_connection, mock_mysql_util):
    mock_db = create_mock_db(fetchOne=None)
    mock_mysql_util.return_value = mock_db
    repo = SkillsRepository()
    result = repo.update_skill('Unknown', {'description': 'Test'})
    assert result is None

@patch('repositories.skills_repository.MysqlUtil')
@patch('repositories.skills_repository.getConnection')
def test_delete_skill(mock_get_connection, mock_mysql_util):
    mock_db = create_mock_db(executeAndCommit=1)
    mock_mysql_util.return_value = mock_db
    repo = SkillsRepository()
    result = repo.delete_skill('Python')
    assert result is True


@patch('repositories.skills_repository.MysqlUtil')
@patch('repositories.skills_repository.getConnection')
def test_list_skills_invalid_json(mock_get_connection, mock_mysql_util):
    mock_db = create_mock_db(fetchAll=[
        ('Python', 'Language', 'not-json', 0, 0, 'Language'),
    ])
    mock_mysql_util.return_value = mock_db
    repo = SkillsRepository()
    skills = repo.list_skills()
    assert len(skills) == 1
    assert skills[0].learning_path == []


@patch('repositories.skills_repository.MysqlUtil')
@patch('repositories.skills_repository.getConnection')
def test_find_by_name_case_insensitive_found(mock_get_connection, mock_mysql_util):
    mock_db = create_mock_db(fetchOne=('Python', 'Language', '["a"]', 0, 1, 'Language'))
    mock_mysql_util.return_value = mock_db
    repo = SkillsRepository()
    result = repo.find_by_name_case_insensitive('python')
    assert result['name'] == 'Python'
    assert result['learning_path'] == ['a']
    assert result['ai_enriched'] is True


@patch('repositories.skills_repository.MysqlUtil')
@patch('repositories.skills_repository.getConnection')
def test_find_by_name_case_insensitive_not_found(mock_get_connection, mock_mysql_util):
    mock_db = create_mock_db(fetchOne=None)
    mock_mysql_util.return_value = mock_db
    repo = SkillsRepository()
    result = repo.find_by_name_case_insensitive('missing')
    assert result is None


@patch('repositories.skills_repository.MysqlUtil')
@patch('repositories.skills_repository.getConnection')
def test_find_by_name_case_insensitive_invalid_json(mock_get_connection, mock_mysql_util):
    mock_db = create_mock_db(fetchOne=('Python', 'Language', 'bad-json', 0, 0, 'Language'))
    mock_mysql_util.return_value = mock_db
    repo = SkillsRepository()
    result = repo.find_by_name_case_insensitive('python')
    assert result['learning_path'] == []


@patch('repositories.skills_repository.MysqlUtil')
@patch('repositories.skills_repository.getConnection')
def test_update_skill_all_fields(mock_get_connection, mock_mysql_util):
    mock_db = create_mock_db(fetchOne=('Python',))
    mock_mysql_util.return_value = mock_db
    repo = SkillsRepository()
    result = repo.update_skill('Python', {
        'description': 'Updated',
        'learning_path': ['x'],
        'disabled': True,
        'ai_enriched': True,
        'category': 'Language',
    })
    assert result == 'Python'
    mock_db.executeAndCommit.assert_called_once()
    query = mock_db.executeAndCommit.call_args[0][0]
    assert 'disabled = %s' in query


@patch('repositories.skills_repository.MysqlUtil')
@patch('repositories.skills_repository.getConnection')
def test_update_skill_learning_path_none(mock_get_connection, mock_mysql_util):
    mock_db = create_mock_db(fetchOne=('Python',))
    mock_mysql_util.return_value = mock_db
    repo = SkillsRepository()
    result = repo.update_skill('Python', {'learning_path': None})
    assert result == 'Python'


@patch('repositories.skills_repository.MysqlUtil')
@patch('repositories.skills_repository.getConnection')
def test_update_skill_no_fields(mock_get_connection, mock_mysql_util):
    mock_db = create_mock_db(fetchOne=('Python',))
    mock_mysql_util.return_value = mock_db
    repo = SkillsRepository()
    result = repo.update_skill('Python', {})
    assert result == 'Python'
    mock_db.executeAndCommit.assert_not_called()
