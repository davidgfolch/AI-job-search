"""Tests for the MySQL readiness wait that replaces crash-looping on resume."""
from unittest.mock import MagicMock, patch

import pytest

from commonlib.sql import db_wait


class TestWaitTimeout:
    @pytest.mark.parametrize('raw, expected', [
        ('5', 5.0), ('', 0.0), ('not-a-number', 0.0),
    ], ids=['seconds', 'unset', 'invalid'])
    def test_env_is_parsed(self, monkeypatch, raw, expected):
        monkeypatch.setenv('COMMONLIB_DB_WAIT_TIMEOUT', raw)
        assert db_wait.wait_timeout() == expected


class TestWaitForDb:
    def test_returns_true_immediately_when_reachable(self):
        log = MagicMock()
        with patch('commonlib.sql.db_wait.time.sleep') as sleep:
            assert db_wait.wait_for_db(timeout=5, log=log, resolve=MagicMock(return_value='mysql_db')) is True
        sleep.assert_not_called()
        assert log.info.call_args[0][0] == 'db.ready'

    def test_retries_until_the_database_answers(self, monkeypatch):
        monkeypatch.setattr(db_wait, 'DB_WAIT_LOG_SECONDS', 0)
        log = MagicMock()
        resolve = MagicMock(side_effect=[ConnectionError('down'), ConnectionError('down'), 'mysql_db'])
        with patch('commonlib.sql.db_wait.time.sleep') as sleep:
            assert db_wait.wait_for_db(timeout=5, interval=0, log=log, resolve=resolve) is True
        assert sleep.call_count == 2
        assert any(call.args[0] == 'db.waiting' for call in log.warning.call_args_list)

    def test_timeout_returns_false(self):
        log = MagicMock()
        with patch('commonlib.sql.db_wait.time.sleep'):
            assert db_wait.wait_for_db(timeout=0.01, interval=0, log=log, resolve=MagicMock(side_effect=ConnectionError('down'))) is False
        assert log.error.call_args[0][0] == 'db.wait_timeout'

    def test_wait_forever_never_times_out(self):
        resolve = MagicMock(side_effect=[ConnectionError('down'), ConnectionError('down'), 'mysql_db'])
        with patch('commonlib.sql.db_wait.time.sleep'):
            assert db_wait.wait_for_db(timeout=0, interval=0, log=MagicMock(), resolve=resolve) is True

    def test_default_resolve_is_the_connection_manager(self, monkeypatch):
        resolve = MagicMock(return_value='mysql_db')
        monkeypatch.setattr('commonlib.sql.connection_manager._resolve_db_host', resolve)
        assert db_wait.wait_for_db(timeout=1, log=MagicMock()) is True
        resolve.assert_called_once()

    def test_interval_and_timeout_come_from_the_environment(self, monkeypatch):
        monkeypatch.setenv('COMMONLIB_DB_WAIT_TIMEOUT', '0.01')
        with patch('commonlib.sql.db_wait.time.sleep') as sleep:
            db_wait.wait_for_db(log=MagicMock(), resolve=MagicMock(side_effect=ConnectionError('down')))
        assert sleep.called
