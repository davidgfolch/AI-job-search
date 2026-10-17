"""Fixtures and readers shared by observability_test."""

import json

import pytest

from commonlib import observability

APP_NAME_ENV = "LOG_APP_NAME"
LEGACY_APP_NAME_ENV = "AI_ENRICH_LOG_APP_NAME"


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    """Redirect the JSONL output to a temp dir and reset the app name."""
    target = tmp_path / "logs"
    monkeypatch.setenv("LOG_DIR", str(target))
    monkeypatch.delenv(APP_NAME_ENV, raising=False)
    monkeypatch.delenv(LEGACY_APP_NAME_ENV, raising=False)
    observability._app_name = None
    yield target
    observability._app_name = None


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.readline().strip()


def _events(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


@pytest.fixture
def fake_app(tmp_path, monkeypatch):
    """A non-commonlib module that emits a record, standing in for a worker's own code."""
    package = tmp_path / "helperpkg"
    package.mkdir()
    (package / "fake_app.py").write_text(
        "from commonlib.observability import stamp_caller_module\n"
        "\n"
        "def emit(event_dict):\n"
        "    return stamp_caller_module(None, 'info', event_dict)\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(package))

    import fake_app as module

    yield module
