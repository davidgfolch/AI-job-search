import os
import sys
import subprocess
import time
import socket
import mysql.connector
import signal
from pathlib import Path

# Configuration
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_USER = 'root'
DB_PASS = 'rootPass'  # Adjust if needed or use env var
DB_NAME_PREFIX = 'jobs_e2e'
DDL_SCRIPT_PATH = 'scripts/mysql/ddl.sql'
BACKEND_DIR = 'apps/backend'
E2E_DIR = 'apps/e2e'

def get_free_port():
    """Finds a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def setup_database(db_name):
    """Creates a fresh database and runs DDL."""
    if db_name == "jobs":
        print("Database for e2e tests name cannot be 'jobs'")
        sys.exit(1)
    print(f"Setting up database: {db_name}")
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor()
        
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        cursor.execute(f"CREATE DATABASE {db_name}")
        cursor.execute(f"USE {db_name}")
        
        # Read and execute DDL
        with open(DDL_SCRIPT_PATH, 'r', encoding='utf-8') as f:
            ddl_content = f.read()
            # Split commands by semicolon (simple approach)
            commands = ddl_content.split(';')
            for cmd in commands:
                if cmd.strip():
                    cursor.execute(cmd)
        
        conn.commit()
        conn.close()
        print(f"Database {db_name} ready.")
    except Exception as e:
        print(f"Database setup failed: {e}")
        sys.exit(1)

def wait_for_backend(port):
    """Waits for backend health check to be green."""
    url = f"http://localhost:{port}/health"
    print(f"Waiting for backend at {url}...")
    # Using curl or python requests would be better, but keeping deps minimal:
    # We'll stick to a simple loop checking the port/endpoint via urllib or requests if available.
    # Since this is a dev script, let's assume standard libs.
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

def run_e2e_tests():
    """Main orchestration function."""
    # 1. Configuration
    port = get_free_port()
    db_name = f"{DB_NAME_PREFIX}_{port}"
    
    # 2. Database Setup
    setup_database(db_name)
    
    # 3. Start Backend
    print(f"Starting backend on port {port} with DB {db_name}...")
    env = os.environ.copy()
    env['DB_NAME'] = db_name
    env['DB_HOST'] = DB_HOST # Ensure host is passed
    
    backend_cmd = ['uv', 'run', 'uvicorn', 'main:app', '--reload', '--port', str(port)]
    
    # Start process
    # Note: running from root, so CWD for backend should be apps/backend? 
    # run.bat/sh does 'cd apps/backend'. Let's mimic that or run from root if imports allow.
    # apps/backend/run.bat cd's into apps/backend. Let's do the same.
    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=BACKEND_DIR,
        env=env,
        # stdout=subprocess.DEVNULL, # Uncomment to silence backend logs
        # stderr=subprocess.DEVNULL
    )
    
    try:
        wait_for_backend(port)
        
        # 4. Run Tests
        print("Running Playwright tests...")
        env['VITE_API_BASE_URL'] = f"http://localhost:{port}/api"
        # Also need detailed reporting?
        
        # We need to run `npm test` in apps/e2e
        # On windows, npm might need shell=True or be called as 'npm.cmd'
        npm_cmd = 'npm.cmd' if os.name == 'nt' else 'npm'
        
        test_result = subprocess.run(
            [npm_cmd, 'test'],
            cwd=E2E_DIR,
            env=env
        )
        
        if test_result.returncode != 0:
            print("Tests failed!")
            sys.exit(test_result.returncode)
        else:
            print("Tests passed!")
            
    finally:
        # 5. Teardown
        print("Stopping backend...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
        
        # Optional: Drop DB? Maybe keep for debugging if failed?
        # For now, let's keep it.

if __name__ == "__main__":
    run_e2e_tests()
