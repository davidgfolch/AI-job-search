"""Patch stack shared by the main.run() tests.

`run()` drives an endless loop over the database, Ollama and the collectors, so every test
patches the same collaborators and only configures the return values it cares about.
"""
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


@pytest.fixture
def loop():
    """The collaborators of `main.run()`, patched and wired to a fake MySQL session."""
    with patch("aiEnrichSkill.main.collector") as collector, \
         patch("aiEnrichSkill.main.wait_for_db"), \
         patch("aiEnrichSkill.main.MysqlUtil") as mysql, \
         patch("aiEnrichSkill.main.get_enabled") as enabled, \
         patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x), \
         patch("aiEnrichSkill.main.get_backend", return_value="ollama"), \
         patch("aiEnrichSkill.main.resolve_ollama_url", return_value="http://host:11434") as resolve, \
         patch("aiEnrichSkill.main.idleWait") as idle, \
         patch("aiEnrichSkill.main.enrich_skills") as enrich, \
         patch("aiEnrichSkill.main.logIdleWait") as log_idle, \
         patch("aiEnrichSkill.main.get_max_ollama_failures", return_value=2), \
         \
         patch("aiEnrichSkill.main.should_run_learning_paths", return_value=False) as should, \
         patch("aiEnrichSkill.main.enrich_learning_paths", return_value=0) as paths, \
         patch("aiEnrichSkill.main.LearningPathScheduler") as scheduler:
        enabled.return_value = True
        mysql.return_value.__enter__.return_value = MagicMock()
        scheduler.return_value.deferred = False
        yield SimpleNamespace(collector=collector, mysql=mysql, enabled=enabled, resolve=resolve, idle=idle,
                             enrich=enrich, log_idle=log_idle, should=should, paths=paths, scheduler=scheduler)
