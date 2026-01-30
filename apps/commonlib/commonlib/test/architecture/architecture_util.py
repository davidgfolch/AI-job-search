
from pathlib import Path

EXTENSIONS = {'.py', '.ts', '.tsx', '.js', '.jsx'}
EXCLUDES = {
    'node_modules', '.venv', 'custom-venv', 'dist', 'build', '.git', 
    '__pycache__', 'coverage', '.next', '.pytest_cache', '.amazonq',
    'READMEs' # Documentation often has large files or isn't code
}

def get_project_root():
    # Assuming this test is in apps/commonlib/test
    current_dir = Path(__file__).resolve().parent
    return current_dir.parent.parent.parent.parent.parent

def count_lines(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0
