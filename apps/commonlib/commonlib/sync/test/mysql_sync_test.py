from unittest.mock import patch, MagicMock

import pytest
from commonlib.sync.mysql_sync import (
    build_dump_cmd, build_restore_cmd, preflight_target, dump_tables,
    make_dump_path, dump_local, restore_target, main,
)


class TestBuildDumpCmd:
    def test_default(self):
        cmd = build_dump_cmd()
        assert cmd == ['docker', 'exec', '-i', '-e', 'MYSQL_PWD=rootPass',
                       'ai-job-search-mysql', '/usr/bin/mysqldump', '-u', 'root',
                       '--single-transaction', '--routines', '--triggers',
                       '--events', '--set-gtid-purged=OFF', 'jobs']

    def test_custom_db(self):
        cmd = build_dump_cmd(db='test_db')
        assert cmd[-1] == 'test_db'


class TestBuildRestoreCmd:
    def test_local(self):
        cmd = build_restore_cmd(host='127.0.0.1')
        assert '-h' not in cmd
        assert cmd[-1] == 'jobs'

    def test_remote(self):
        cmd = build_restore_cmd(host='192.168.1.50')
        h_idx = cmd.index('-h')
        assert cmd[h_idx + 1] == '192.168.1.50'
        assert cmd[-1] == 'jobs'


class TestPreflightTarget:
    @patch('commonlib.sync.mysql_sync._run')
    def test_success(self, mock_run):
        mock_run.return_value = (0, '', '')
        preflight_target('192.168.1.50')
        args = mock_run.call_args[0][0]
        assert '-h' in args and '192.168.1.50' in args

    @patch('commonlib.sync.mysql_sync._run')
    def test_failure(self, mock_run):
        mock_run.return_value = (1, '', 'access denied')
        with pytest.raises(ConnectionError):
            preflight_target('192.168.1.50')


class TestDumpTables:
    def test_parses(self, tmp_path):
        f = tmp_path / "dump.sql"
        f.write_text("CREATE TABLE `jobs` (...)\nCREATE TABLE `job_skills` (...)\n")
        assert dump_tables(f) == ['jobs', 'job_skills']


class TestMakeDumpPath:
    def test_creates_dir(self, tmp_path):
        d = tmp_path / 'sub'
        path = make_dump_path(d)
        assert path.parent == d
        assert path.name.endswith('_sync_backup.sql')
        assert d.exists()

    def test_custom_name(self, tmp_path):
        path = make_dump_path(tmp_path)
        assert path.suffix == '.sql'


class TestDumpLocal:
    @patch('commonlib.sync.mysql_sync._run')
    def test_success(self, mock_run, tmp_path):
        mock_run.return_value = (0, '', '')
        dump_file = tmp_path / "out.sql"
        summary = dump_local(dump_file)
        assert summary['tables'] == []
        assert summary['size_mb'] == 0.0
        assert summary['file'] == str(dump_file)

    @patch('commonlib.sync.mysql_sync._run')
    def test_failure(self, mock_run, tmp_path):
        mock_run.return_value = (1, '', 'dump error')
        with pytest.raises(RuntimeError, match='dump error'):
            dump_local(tmp_path / "out.sql")


class TestRestoreTarget:
    @patch('commonlib.sync.mysql_sync._run')
    def test_success(self, mock_run, tmp_path):
        mock_run.return_value = (0, '', '')
        dump_file = tmp_path / "dump.sql"
        dump_file.write_text("-- dump\n")
        restore_target(dump_file, '192.168.1.50')
        args = mock_run.call_args[0][0]
        assert '-h' in args and '192.168.1.50' in args

    @patch('commonlib.sync.mysql_sync._run')
    def test_failure(self, mock_run, tmp_path):
        mock_run.return_value = (1, '', 'restore error')
        dump_file = tmp_path / "dump.sql"
        dump_file.write_text("-- dump\n")
        with pytest.raises(RuntimeError, match='restore error'):
            restore_target(dump_file, '192.168.1.50')


class TestMain:
    @patch('commonlib.sync.mysql_sync.dump_local', return_value={'file': '/tmp/d.sql', 'tables': ['jobs'], 'size_mb': 1.0})
    @patch('commonlib.sync.mysql_sync.preflight_target')
    @patch('commonlib.sync.mysql_sync.resolve_mysql_host', return_value='192.168.1.50')
    def test_dry_run_skips_restore(self, mock_resolve, mock_pre, mock_dump):
        rc = main(['--dry-run', '192.168.1.50'])
        assert rc == 0
        mock_dump.assert_called_once()

    @patch('commonlib.sync.mysql_sync.restore_target')
    @patch('commonlib.sync.mysql_sync.confirm', return_value=False)
    @patch('commonlib.sync.mysql_sync.dump_local', return_value={'file': '/tmp/d.sql', 'tables': [], 'size_mb': 0.1})
    @patch('commonlib.sync.mysql_sync.preflight_target')
    @patch('commonlib.sync.mysql_sync.resolve_mysql_host', return_value='192.168.1.50')
    def test_aborted_by_user(self, mock_resolve, mock_pre, mock_dump, mock_conf, mock_restore):
        rc = main(['192.168.1.50'])
        assert rc == 1
        mock_restore.assert_not_called()

    @patch('commonlib.sync.mysql_sync.restore_target')
    @patch('commonlib.sync.mysql_sync.dump_local', return_value={'file': '/tmp/d.sql', 'tables': [], 'size_mb': 0.1})
    @patch('commonlib.sync.mysql_sync.preflight_target')
    @patch('commonlib.sync.mysql_sync.resolve_mysql_host', return_value='192.168.1.50')
    def test_yes_skips_confirm(self, mock_resolve, mock_pre, mock_dump, mock_restore):
        rc = main(['--yes', '192.168.1.50'])
        assert rc == 0
        mock_restore.assert_called_once()
