from unittest.mock import MagicMock

from ..skill_context_helper import fetch_skill_context_safe


def test_fetch_skill_context_safe_returns_context():
    repository = MagicMock()
    repository.fetch_skill_context.return_value = "Django, Flask"
    assert fetch_skill_context_safe(repository, "Python") == "Django, Flask"
    repository.fetch_skill_context.assert_called_once_with("Python")


def test_fetch_skill_context_safe_degrades_to_empty():
    repository = MagicMock()
    repository.fetch_skill_context.side_effect = RuntimeError("db down")
    assert fetch_skill_context_safe(repository, "Python") == ""
