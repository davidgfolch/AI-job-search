import pytest
from unittest.mock import patch, MagicMock

from ..main import run


@patch("aiEnrichSkill.main.collector")
@patch("aiEnrichSkill.main.idleWait")
@patch("aiEnrichSkill.main.enrich_skills")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_disabled(mock_cyan, mock_enabled, mock_mysql, mock_enrich, mock_idle, mock_collector):
    mock_enabled.return_value = False

    run()

    mock_mysql.assert_not_called()
    mock_enrich.assert_not_called()
    mock_collector.persist.assert_not_called()


@patch("aiEnrichSkill.main.collector")
@patch("aiEnrichSkill.main.get_backend", return_value="ollama")
@patch("aiEnrichSkill.main.resolve_ollama_url", return_value="http://host:11434")
@patch("aiEnrichSkill.main.idleWait")
@patch("aiEnrichSkill.main.enrich_skills")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_enriched_some_skills(mock_cyan, mock_enabled, mock_mysql_cls, mock_enrich, mock_idle, mock_resolve, mock_backend, mock_collector):
    mock_enabled.return_value = True
    mysql = MagicMock()
    mock_mysql_cls.return_value.__enter__.return_value = mysql
    mock_enrich.side_effect = [3, 0, Exception("BreakLoop")]

    try:
        run()
    except Exception as e:
        if str(e) != "BreakLoop":
            raise e

    assert mock_enrich.call_count == 3
    mock_collector.persist.assert_called()


@patch("aiEnrichSkill.main.collector")
@patch("aiEnrichSkill.main.get_backend", return_value="ollama")
@patch("aiEnrichSkill.main.resolve_ollama_url", return_value="http://host:11434")
@patch("aiEnrichSkill.main.idleWait")
@patch("aiEnrichSkill.main.enrich_skills")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_no_skills_waits(mock_cyan, mock_enabled, mock_mysql_cls, mock_enrich, mock_idle, mock_resolve, mock_backend, mock_collector):
    mock_enabled.return_value = True
    mysql = MagicMock()
    mock_mysql_cls.return_value.__enter__.return_value = mysql
    mock_enrich.side_effect = [0, Exception("BreakLoop")]

    try:
        run()
    except Exception as e:
        if str(e) != "BreakLoop":
            raise e

    mock_idle.assert_called_once()
    assert mock_idle.call_args.args == ("All skills enriched.", "10s")
    assert mock_idle.call_args.kwargs == {}
    mock_collector.persist.assert_called_once()
    mock_collector.record_heartbeat.assert_called_with("aiEnrichSkill")


@patch("aiEnrichSkill.main.collector")
@patch("aiEnrichSkill.main.get_backend", return_value="ollama")
@patch("aiEnrichSkill.main.resolve_ollama_url", return_value=None)
@patch("aiEnrichSkill.main.logIdleWait")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.get_max_ollama_failures", return_value=2)
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_unreachable_backend_waits_before_enriching(mock_cyan, mock_max, mock_enabled, mock_mysql_cls, mock_idle, mock_resolve, mock_backend, mock_collector):
    mock_enabled.return_value = True
    mock_mysql_cls.return_value.__enter__.return_value = MagicMock()

    # The second unreachable poll trips the exit threshold, which ends the loop.
    with pytest.raises(SystemExit):
        run()

    mock_idle.assert_called_once()
    assert mock_idle.call_args.args[1:] == ("10s", "ai.retry_wait")
    assert mock_idle.call_args.kwargs == {"reason": "backend_unavailable"}


@patch("aiEnrichSkill.main.collector")
@patch("aiEnrichSkill.main.get_backend", return_value="ollama")
@patch("aiEnrichSkill.main.resolve_ollama_url", return_value="http://host:11434")
@patch("aiEnrichSkill.main.idleWait")
@patch("aiEnrichSkill.main.enrich_skills")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_persists_after_each_enrich_cycle(mock_cyan, mock_enabled, mock_mysql_cls, mock_enrich, mock_idle, mock_resolve, mock_backend, mock_collector):
    mock_enabled.return_value = True
    mysql = MagicMock()
    mock_mysql_cls.return_value.__enter__.return_value = mysql
    mock_enrich.side_effect = [5, 2, 0, Exception("BreakLoop")]

    try:
        run()
    except Exception as e:
        if str(e) != "BreakLoop":
            raise e

    assert mock_collector.persist.call_count == 3