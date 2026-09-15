import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from commonlib.network.mysql_discovery import resolve_mysql_host
from commonlib.terminalColor import green, red, yellow

CONTAINER = os.getenv('MYSQL_SYNC_CONTAINER', 'ai-job-search-mysql')
MYSQL_PWD = os.getenv('MYSQL_SYNC_PASSWORD', 'rootPass')
DB_NAME = os.getenv('COMMONLIB_DB_NAME', 'jobs')
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DUMP_DIR = REPO_ROOT / 'scripts' / 'mysql' / 'backups'
MYSQLDUMP_FLAGS = ['--single-transaction', '--routines', '--triggers', '--events', '--set-gtid-purged=OFF']
CREATE_TABLE_RE = re.compile(r"CREATE TABLE `([^`]+)`")


def _run(cmd, stdin_file=None, stdout_file=None):
    """Run a subprocess; returns (returncode, stdout_text, stderr_text)."""
    result = subprocess.run(cmd, stdin=stdin_file, stdout=stdout_file, stderr=subprocess.PIPE, text=True)
    return result.returncode, result.stdout or '', result.stderr or ''


def build_dump_cmd(container=CONTAINER, db=DB_NAME, pwd=MYSQL_PWD):
    """docker exec mysqldump command to dump the local DB."""
    return ['docker', 'exec', '-i', '-e', f'MYSQL_PWD={pwd}', container,
            '/usr/bin/mysqldump', '-u', 'root', *MYSQLDUMP_FLAGS, db]


def build_restore_cmd(host='127.0.0.1', container=CONTAINER, db=DB_NAME, pwd=MYSQL_PWD):
    """docker exec mysql command applying a dump onto the target host."""
    cmd = ['docker', 'exec', '-i', '-e', f'MYSQL_PWD={pwd}', container, '/usr/bin/mysql', '-u', 'root']
    if host != '127.0.0.1':
        cmd += ['-h', host]
    cmd.append(db)
    return cmd


def preflight_target(host, container=CONTAINER, db=DB_NAME, pwd=MYSQL_PWD):
    """Verify root/TCP connectivity to the target host before restoring. Raises on failure."""
    cmd = ['docker', 'exec', '-e', f'MYSQL_PWD={pwd}', container, '/usr/bin/mysql', '-u', 'root']
    if host != '127.0.0.1':
        cmd += ['-h', host]
    cmd += ['-e', 'SELECT 1', db]
    code, _, err = _run(cmd)
    if code != 0:
        raise ConnectionError(f"Target {host} MySQL not reachable with root (is port 3306 exposed and root allowed?): {err.strip()}")


def dump_tables(dump_file):
    """Return table names found in a mysqldump file."""
    return CREATE_TABLE_RE.findall(dump_file.read_text(encoding='utf-8', errors='replace'))


def make_dump_path(dump_dir=None):
    dump_dir = Path(dump_dir or DEFAULT_DUMP_DIR)
    dump_dir.mkdir(parents=True, exist_ok=True)
    return dump_dir / f"{datetime.now():%Y%m%d_%H%M%S}_sync_backup.sql"


def dump_local(dump_file, container=CONTAINER, db=DB_NAME, pwd=MYSQL_PWD):
    """Dump local DB to dump_file; returns a summary dict."""
    print(green(f"Dumping local '{db}' DB to {dump_file}..."))
    with open(dump_file, 'w') as fh:
        code, _, err = _run(build_dump_cmd(container, db, pwd), stdout_file=fh)
    if code != 0:
        raise RuntimeError(f"mysqldump failed: {err.strip()}")
    tables = dump_tables(dump_file)
    size_mb = dump_file.stat().st_size / (1024 * 1024)
    return {'file': str(dump_file), 'tables': tables, 'size_mb': round(size_mb, 1)}


def restore_target(dump_file, host, container=CONTAINER, db=DB_NAME, pwd=MYSQL_PWD):
    """Apply the dump onto the target host (full replace of the DB)."""
    print(green(f"Restoring {db} onto {host} (full replace)..."))
    with open(dump_file) as fh:
        code, _, err = _run(build_restore_cmd(host, container, db, pwd), stdin_file=fh)
    if code != 0:
        raise RuntimeError(f"restore onto {host} failed: {err.strip()}")
    print(green(f"Restore onto {host} completed successfully."))


def summarize(target, summary, db):
    print(yellow("Dry-run summary"))
    print(f"  Target:   {target}")
    print(f"  Database: {db}")
    print(f"  Dump:     {summary['file']} ({summary['size_mb']} MB, {len(summary['tables'])} tables)")
    print(f"  Action:   full replace of '{db}' on {target}")


def confirm(target, db, yes=False):
    if yes:
        return True
    answer = input(f"Restore '{db}' onto {target}? Any data there not in the dump will be lost. [y/N]: ")
    return answer.strip().lower() in ('y', 'yes')


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Dump the local 'jobs' DB and full-restore it onto the other machine (no arg = auto-discover target).")
    parser.add_argument('target', nargs='?', default='auto',
                        help="target MySQL IP, or 'auto' to discover it on the LAN (default: auto)")
    parser.add_argument('--db', default=DB_NAME, help=f"database name (default: {DB_NAME})")
    parser.add_argument('--dry-run', action='store_true', help="dump + summary only, don't restore")
    parser.add_argument('--yes', action='store_true', help="skip the confirmation prompt")
    args = parser.parse_args(argv)

    print(yellow(f"Resolving target MySQL (spec: {args.target})..."))
    target = resolve_mysql_host(args.target)
    print(green(f"Target MySQL at {target}"))
    preflight_target(target, db=args.db)

    dump_file = make_dump_path()
    summary = dump_local(dump_file, db=args.db)
    summarize(target, summary, args.db)

    if args.dry_run:
        print(yellow("Dry run: not restoring."))
        return 0
    if not confirm(target, args.db, yes=args.yes):
        print(red("Restore aborted by user."))
        return 1

    restore_target(dump_file, target, db=args.db)
    return 0


if __name__ == '__main__':
    sys.exit(main())