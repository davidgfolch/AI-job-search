
import os
from pathlib import Path

EXTENSIONS = {'.py', '.ts', '.tsx', '.js', '.jsx'}
EXCLUDES = {
    'node_modules', '.venv', 'custom-venv', 'dist', 'build', '.git', 
    '__pycache__', 'coverage', '.next', '.pytest_cache', '.amazonq',
    'READMEs', # Documentation often has large files or isn't code
    '.vite', # Vite dependency cache
}

def get_project_root():
    # Assuming this test is in apps/commonlib/test
    current_dir = Path(__file__).resolve().parent
    return current_dir.parent.parent.parent.parent.parent

def iter_source_files(base_dir, extensions=EXTENSIONS):
    # os.walk prunes excluded dirs before descending, unlike rglob which
    # traverses .venv/node_modules/custom-venv only to discard them afterwards.
    base_dir = Path(base_dir)
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDES]
        for name in files:
            if Path(name).suffix in extensions:
                yield Path(root) / name

def count_lines(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0
