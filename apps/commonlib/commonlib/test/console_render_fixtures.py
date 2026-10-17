"""Fixtures and readers shared by console_render_test."""

import json

import pytest

from commonlib import console_render, observability

LEGACY_ENV = ("AI_ENRICH_LOG_CONSOLE_MODE",)


@pytest.fixture
def console(tmp_path, monkeypatch):
    """Redirect the JSONL output, reset the app name and the console mode."""
    target = tmp_path / "logs"
    monkeypatch.setenv("LOG_DIR", str(target))
    monkeypatch.delenv("AI_ENRICH_LOG_DIR", raising=False)
    for name in ("LOG_CONSOLE_MODE", *LEGACY_ENV):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("LOG_COLOR", raising=False)
    observability._app_name = None
    console_render.set_console_mode(None)
    yield target
    observability._app_name = None
    console_render.set_console_mode(None)


def _events(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]
