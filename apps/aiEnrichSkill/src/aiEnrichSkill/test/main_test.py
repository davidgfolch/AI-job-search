import inspect

import pytest
from unittest.mock import patch, MagicMock

from commonlib.ai_helpers import idleWait as real_idle_wait
from ..main import run


@pytest.fixture(autouse=True)
def no_real_learning_path_pass():
    """The loop's idle branch must never touch a real database or model in these tests."""
    with patch("aiEnrichSkill.main.enrich_learning_paths", return_value=0):
        yield


@patch("aiEnrichSkill.main.collector")
@patch("aiEnrichSkill.main.wait_for_db")
@patch("aiEnrichSkill.main.idleWait")
@patch("aiEnrichSkill.main.enrich_skills")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_disabled(mock_cyan, mock_enabled, mock_mysql, mock_enrich, mock_idle, _mock_wait, mock_collector):
    mock_enabled.return_value = False

    run()

    mock_mysql.assert_not_called()
    mock_enrich.assert_not_called()
    mock_collector.persist.assert_not_called()


@patch("aiEnrichSkill.main.collector")
@patch("aiEnrichSkill.main.wait_for_db")
@patch("aiEnrichSkill.main.get_backend", return_value="ollama")
@patch("aiEnrichSkill.main.resolve_ollama_url", return_value="http://host:11434")
@patch("aiEnrichSkill.main.idleWait")
@patch("aiEnrichSkill.main.enrich_skills")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_enriched_some_skills(mock_cyan, mock_enabled, mock_mysql_cls, mock_enrich, mock_idle, mock_resolve, mock_backend, _mock_wait, mock_collector):
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
@patch("aiEnrichSkill.main.wait_for_db")
@patch("aiEnrichSkill.main.get_backend", return_value="ollama")
@patch("aiEnrichSkill.main.resolve_ollama_url", return_value="http://host:11434")
@patch("aiEnrichSkill.main.idleWait")
@patch("aiEnrichSkill.main.enrich_skills")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_no_skills_waits(mock_cyan, mock_enabled, mock_mysql_cls, mock_enrich, mock_idle, mock_resolve, mock_backend, _mock_wait, mock_collector):
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
    # The mock hides the real signature: bind against the helper the loop actually calls.
    inspect.signature(real_idle_wait).bind(*mock_idle.call_args.args, **mock_idle.call_args.kwargs)
    mock_collector.persist.assert_called_once()
    mock_collector.record_heartbeat.assert_called_with("aiEnrichSkill")


@patch("aiEnrichSkill.main.collector")
@patch("aiEnrichSkill.main.logger")
@patch("aiEnrichSkill.main.wait_for_db")
@patch("aiEnrichSkill.main.get_backend", return_value="ollama")
@patch("aiEnrichSkill.main.resolve_ollama_url", side_effect=[None, None, "http://host:11434"])
@patch("aiEnrichSkill.main.logIdleWait")
@patch("aiEnrichSkill.main.enrich_skills", side_effect=Exception("BreakLoop"))
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.get_max_ollama_failures", return_value=2)
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_unreachable_backend_waits_before_enriching(
    mock_cyan, mock_max, mock_enabled, mock_mysql_cls, _mock_enrich, mock_idle, _mock_resolve, _mock_backend, _mock_wait, mock_logger, mock_collector
):
    mock_enabled.return_value = True
    mock_mysql_cls.return_value.__enter__.return_value = MagicMock()

    # Past the failure threshold the worker keeps waiting instead of exiting
    # (exiting here turned a sleeping Ollama into a container restart storm).
    with pytest.raises(Exception, match="BreakLoop"):
        run()

    assert mock_idle.call_count == 2
    assert mock_idle.call_args.args[1:] == ("10s", "ai.retry_wait")
    assert mock_idle.call_args.kwargs == {"reason": "backend_unavailable"}
    assert mock_logger.critical.call_args.args[0] == "ollama.waiting_after_failures"


@patch("aiEnrichSkill.main.collector")
@patch("aiEnrichSkill.main.wait_for_db")
@patch("aiEnrichSkill.main.get_backend", return_value="ollama")
@patch("aiEnrichSkill.main.resolve_ollama_url", return_value="http://host:11434")
@patch("aiEnrichSkill.main.idleWait")
@patch("aiEnrichSkill.main.enrich_skills")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_persists_after_each_enrich_cycle(mock_cyan, mock_enabled, mock_mysql_cls, mock_enrich, mock_idle, mock_resolve, mock_backend, _mock_wait, mock_collector):
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

@patch("aiEnrichSkill.main.enrich_learning_paths", return_value=1)
@patch("aiEnrichSkill.main.should_run_learning_paths", return_value=True)
@patch("aiEnrichSkill.main.collector")
@patch("aiEnrichSkill.main.wait_for_db")
@patch("aiEnrichSkill.main.get_backend", return_value="ollama")
@patch("aiEnrichSkill.main.resolve_ollama_url", return_value="http://host:11434")
@patch("aiEnrichSkill.main.idleWait")
@patch("aiEnrichSkill.main.enrich_skills")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_idle_pass_backfills_learning_paths(
    mock_cyan, mock_enabled, mock_mysql_cls, mock_enrich, mock_idle, mock_resolve, mock_backend,
    _mock_wait, mock_collector, mock_should, mock_paths
):
    mock_enabled.return_value = True
    mysql = MagicMock()
    mock_mysql_cls.return_value.__enter__.return_value = mysql
    mock_enrich.side_effect = [0, Exception("BreakLoop")]

    try:
        run()
    except Exception as e:
        if str(e) != "BreakLoop":
            raise e

    mock_should.assert_called_once()
    mock_paths.assert_called_once()
    assert mock_paths.call_args.kwargs["ollama_base_url"] == "http://host:11434"
    assert "scheduler" in mock_paths.call_args.kwargs
    mock_idle.assert_not_called()
    mock_collector.persist.assert_called_once()


@patch("aiEnrichSkill.main.enrich_learning_paths")
@patch("aiEnrichSkill.main.should_run_learning_paths", return_value=False)
@patch("aiEnrichSkill.main.collector")
@patch("aiEnrichSkill.main.wait_for_db")
@patch("aiEnrichSkill.main.get_backend", return_value="ollama")
@patch("aiEnrichSkill.main.resolve_ollama_url", return_value="http://host:11434")
@patch("aiEnrichSkill.main.idleWait")
@patch("aiEnrichSkill.main.enrich_skills")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_skips_idle_pass_when_gate_is_closed(
    mock_cyan, mock_enabled, mock_mysql_cls, mock_enrich, mock_idle, mock_resolve, mock_backend,
    _mock_wait, mock_collector, mock_should, mock_paths
):
    mock_enabled.return_value = True
    mock_mysql_cls.return_value.__enter__.return_value = MagicMock()
    mock_enrich.side_effect = [0, Exception("BreakLoop")]

    try:
        run()
    except Exception as e:
        if str(e) != "BreakLoop":
            raise e

    mock_should.assert_called_once()
    mock_paths.assert_not_called()
    mock_idle.assert_called_once()


@patch("aiEnrichSkill.main.LearningPathScheduler")
@patch("aiEnrichSkill.main.enrich_learning_paths", return_value=0)
@patch("aiEnrichSkill.main.should_run_learning_paths", return_value=True)
@patch("aiEnrichSkill.main.collector")
@patch("aiEnrichSkill.main.wait_for_db")
@patch("aiEnrichSkill.main.get_backend", return_value="ollama")
@patch("aiEnrichSkill.main.resolve_ollama_url", return_value="http://host:11434")
@patch("aiEnrichSkill.main.idleWait")
@patch("aiEnrichSkill.main.enrich_skills")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_retries_quickly_while_the_model_is_busy(
    mock_cyan, mock_enabled, mock_mysql_cls, mock_enrich, mock_idle, mock_resolve, mock_backend,
    _mock_wait, mock_collector, mock_should, _mock_paths, mock_scheduler
):
    mock_enabled.return_value = True
    mock_mysql_cls.return_value.__enter__.return_value = MagicMock()
    mock_enrich.side_effect = [0, Exception("BreakLoop")]
    mock_scheduler.return_value.deferred = True

    try:
        run()
    except Exception as e:
        if str(e) != "BreakLoop":
            raise e

    mock_idle.assert_called_once()
    assert mock_idle.call_args.args == ("Ollama busy, waiting for a free slot.", "3s")
    assert mock_idle.call_args.kwargs == {}
    inspect.signature(real_idle_wait).bind(*mock_idle.call_args.args, **mock_idle.call_args.kwargs)
