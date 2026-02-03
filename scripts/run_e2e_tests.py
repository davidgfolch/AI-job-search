import os
import sys
import subprocess
import time
import socket
import mysql.connector
import signal
from pathlib import Path
# Add project root to sys.path to allow imports from apps
sys.path.append(str(Path(__file__).resolve().parent.parent))
from apps.commonlib.commonlib.mysqlUtil import getConnection

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
DB_NAME_PREFIX = 'jobs_e2e'
DDL_SCRIPT_PATH = 'scripts/mysql/ddl.sql'
BACKEND_DIR = 'apps/backend'
E2E_DIR = 'apps/e2e'

def get_free_port():
    """Finds a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def get_e2e_connection():
    return getConnection(e2eTests=True)

def setup_database(db_name):
    """Creates a fresh database and runs DDL."""
    if db_name == "jobs":
        print("Database for e2e tests name cannot be 'jobs'")
        sys.exit(1)
    print(f"Setting up database: {db_name}")
    conn = None
    try:
        conn = get_e2e_connection()
        cursor = conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        cursor.execute(f"CREATE DATABASE {db_name}")
        cursor.execute(f"USE {db_name}")
        with open(DDL_SCRIPT_PATH, 'r', encoding='utf-8') as f:
            ddl_content = f.read()
            commands = ddl_content.split(';')
            for cmd in commands:
                if cmd.strip():
                    cursor.execute(cmd)
        conn.commit()
        print(f"Database {db_name} ready.")
    except Exception as e:
        print(f"Database setup failed: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

def cleanup_all_e2e_databases():
    """Finds and drops all test databases matching jobs_e2e_* pattern."""
    import re
    print(f"Cleaning up all {DB_NAME_PREFIX}_* databases...")
    conn = None
    try:
        conn = get_e2e_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        pattern = re.compile(f"^{DB_NAME_PREFIX}_\\d+$")
        e2e_databases = [db for db in databases if pattern.match(db)]
        if not e2e_databases:
            print(f"No {DB_NAME_PREFIX}_* databases found.")
        else:
            for db in e2e_databases:
                print(f"Dropping database: {db}")
                cursor.execute(f"DROP DATABASE IF EXISTS {db}")
                conn.commit()
            print(f"Successfully dropped {len(e2e_databases)} database(s).")
    except Exception as e:
        print(f"Database cleanup failed: {e}")
    finally:
        if conn:
            conn.close()

def wait_for_backend(port):
    """Waits for backend health check to be green."""
    url = f"http://localhost:{port}/health"
    print(f"Waiting for backend at {url}...")
    import urllib.request
    start_time = time.time()
    while time.time() - start_time < 30: # 30 seconds timeout
        try:
            with urllib.request.urlopen(url) as response:
                if response.getcode() == 200:
                    print("Backend is up!")
                    return
        except Exception:
            time.sleep(1)
    print("Backend failed to start in time.")
    sys.exit(1)

def run_e2e_tests(args):
    """Main orchestration function."""
    port = get_free_port()
    db_name = f"{DB_NAME_PREFIX}_{port}"
    setup_database(db_name)
    print(f"Starting backend on port {port} with DB {db_name}...")
    env = os.environ.copy()
    env['DB_NAME'] = db_name
    env['DB_HOST'] = os.getenv('DB_HOST', '127.0.0.1')
    backend_cmd = ['uv', 'run', 'uvicorn', 'main:app', '--reload', '--port', str(port)]
    # Start process
    # Note: running from root, so CWD for backend should be apps/backend? 
    # run.bat/sh does 'cd apps/backend'. Let's mimic that or run from root if imports allow.
    # apps/backend/run.bat cd's into apps/backend. Let's do the same.
    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=BACKEND_DIR,
        env=env,
        stdout=None if DEBUG else subprocess.DEVNULL,
        stderr=None if DEBUG else subprocess.DEVNULL,
    )
    test_passed = False
    try:
        wait_for_backend(port)
        print("Running Playwright tests...")
        env['VITE_API_BASE_URL'] = f"http://localhost:{port}/api"
        npm_cmd = 'npm.cmd' if os.name == 'nt' else 'npm'
        
        # Pass additional arguments to npm test
        # Note: npm test -- <args> passes args to the script
        cmd = [npm_cmd, 'test']
        if args:
             cmd.append('--')
             cmd.extend(args)
             
        test_result = subprocess.run(
            cmd,
            cwd=E2E_DIR,
            env=env
        )
        if test_result.returncode != 0:
            print("Tests failed!")
            sys.exit(test_result.returncode)
        else:
            print("Tests passed!")
            test_passed = True
    finally:
        print("Stopping backend...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
        if test_passed:
            cleanup_all_e2e_databases()
        else:
            print(f"Keeping database {db_name} for debugging.")


if __name__ == "__main__":
    run_e2e_tests(sys.argv[1:])
