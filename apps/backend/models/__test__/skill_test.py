import pytest
from models.skill import Skill, SkillBase, SkillCreate, SkillUpdate

def test_skill_base_creation():
    skill = SkillBase(name="Python", description="Programming language")
    assert skill.name == "Python"
    assert skill.description == "Programming language"
    assert skill.disabled == False

def test_skill_creation():
    skill = Skill(name="Python", description="Language", learning_path=["basics", "advanced"], disabled=False)
    assert skill.name == "Python"
    assert len(skill.learning_path) == 2

def test_skill_create():
    skill = SkillCreate(name="JavaScript", description="Web language")
    assert skill.name == "JavaScript"
    assert skill.description == "Web language"

@pytest.mark.parametrize("name,description,disabled", [
    ("Python", "Programming", False),
    ("Java", "Enterprise", True),
    ("TypeScript", "Typed JS", False)
])
def test_skill_with_params(name, description, disabled):
    skill = Skill(name=name, description=description, disabled=disabled)
    assert skill.name == name
    assert skill.description == description
    assert skill.disabled == disabled

def test_skill_update():
    skill = SkillUpdate(description="Updated description")
    assert skill.description == "Updated description"
    assert skill.name is None
