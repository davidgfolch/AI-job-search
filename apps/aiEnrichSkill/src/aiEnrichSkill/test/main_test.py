import inspect

import pytest
from unittest.mock import patch

from commonlib.ai_helpers import idleWait as real_idle_wait
from ..main import run
from .main_fixtures import loop  # noqa: F401 - the fixture registers by being imported here


def _run_until_break():
    """`run()` never returns on its own, so a test drives the loop and ends it with an exception."""
    with pytest.raises(Exception, match="BreakLoop"):
        run()


def test_run_disabled(loop):
    loop.enabled.return_value = False

    run()

    loop.mysql.assert_not_called()
    loop.enrich.assert_not_called()
    loop.collector.persist.assert_not_called()


def test_run_enriched_some_skills(loop):
    loop.enrich.side_effect = [3, 0, Exception("BreakLoop")]

    _run_until_break()

    assert loop.enrich.call_count == 3
    loop.collector.persist.assert_called()


def test_run_no_skills_waits(loop):
    loop.enrich.side_effect = [0, Exception("BreakLoop")]

    _run_until_break()

    loop.idle.assert_called_once()
    assert loop.idle.call_args.args == ("All skills enriched.", "10s")
    assert loop.idle.call_args.kwargs == {}
    # The mock hides the real signature: bind against the helper the loop actually calls.
    inspect.signature(real_idle_wait).bind(*loop.idle.call_args.args, **loop.idle.call_args.kwargs)
    loop.collector.persist.assert_called_once()
    loop.collector.record_heartbeat.assert_called_with("aiEnrichSkill")


@patch("aiEnrichSkill.main.logger")
def test_run_unreachable_backend_waits_before_enriching(mock_logger, loop):
    loop.resolve.side_effect = [None, None, "http://host:11434"]
    loop.enrich.side_effect = Exception("BreakLoop")

    # Past the failure threshold the worker keeps waiting instead of exiting
    # (exiting here turned a sleeping Ollama into a container restart storm).
    _run_until_break()

    assert loop.log_idle.call_count == 2
    assert loop.log_idle.call_args.args[1:] == ("10s", "ai.retry_wait")
    assert loop.log_idle.call_args.kwargs == {"reason": "backend_unavailable"}
    assert mock_logger.critical.call_args.args[0] == "ollama.waiting_after_failures"


def test_run_resolves_ollama_after_live_backend_switch(loop):
    loop.backend.side_effect = ["huggingface", "ollama", "ollama"]
    loop.enrich.side_effect = [0, Exception("BreakLoop")]

    _run_until_break()

    # No resolution at startup (HuggingFace), one when the selector switches to Ollama.
    loop.resolve.assert_called_once()
    assert loop.enrich.call_count == 2


def test_run_persists_after_each_enrich_cycle(loop):
    loop.enrich.side_effect = [5, 2, 0, Exception("BreakLoop")]

    _run_until_break()

    assert loop.collector.persist.call_count == 3


def test_run_idle_pass_backfills_learning_paths(loop):
    loop.should.return_value = True
    loop.paths.return_value = 1
    loop.enrich.side_effect = [0, Exception("BreakLoop")]

    _run_until_break()

    loop.should.assert_called_once()
    loop.paths.assert_called_once()
    assert loop.paths.call_args.kwargs["ollama_base_url"] == "http://host:11434"
    assert "scheduler" in loop.paths.call_args.kwargs
    loop.idle.assert_not_called()
    loop.collector.persist.assert_called_once()


def test_run_skips_idle_pass_when_gate_is_closed(loop):
    loop.enrich.side_effect = [0, Exception("BreakLoop")]

    _run_until_break()

    loop.should.assert_called_once()
    loop.paths.assert_not_called()
    loop.idle.assert_called_once()


def test_run_retries_quickly_while_the_model_is_busy(loop):
    loop.should.return_value = True
    loop.enrich.side_effect = [0, Exception("BreakLoop")]
    loop.scheduler.return_value.deferred = True

    _run_until_break()

    loop.idle.assert_called_once()
    assert loop.idle.call_args.args == ("Ollama busy, waiting for a free slot.", "3s")
    assert loop.idle.call_args.kwargs == {}
    inspect.signature(real_idle_wait).bind(*loop.idle.call_args.args, **loop.idle.call_args.kwargs)
