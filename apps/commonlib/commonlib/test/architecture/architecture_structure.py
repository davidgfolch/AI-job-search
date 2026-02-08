
import os
from pathlib import Path
from commonlib.test.architecture.architecture_util import get_project_root, EXCLUDES

def get_files_without_sibling_test():
    root_dir = get_project_root()
    apps_dir = root_dir / 'apps'
    if not apps_dir.exists():
        return []
    violations = []
    IGNORED_FILES = {'__init__.py', 'conftest.py', 'setup.py', 'main.py'}
    SKIP_DIRS = {
        'node_modules', '.venv', 'custom-venv', 'dist', 'build', '.git', 
        '__pycache__', 'coverage', '.pytest_cache', 'test'
    }
    INVALID_TEST_DIRS = {'__test__', 'tests', '__tests__'}
    for root, dirs, files in os.walk(apps_dir):
        for d in dirs:
            if d in INVALID_TEST_DIRS:
                dir_path = Path(root) / d
                has_py = False
                try:
                    for p_root, _, p_files in os.walk(dir_path):
                         if any(f.endswith('.py') for f in p_files):
                             has_py = True
                             break
                except Exception:
                    pass
                if has_py:
                    violations.append((str(dir_path), f"Invalid test folder name '{d}'. Rename to 'test'."))
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d not in EXCLUDES and d not in INVALID_TEST_DIRS]
        if Path(root).name == 'test':
            continue
        for filename in files:
            if not filename.endswith('.py'):
                continue
            if filename in IGNORED_FILES:
                continue
            if filename.startswith('test_') or filename.endswith('_test.py'):
                continue
            path = Path(root) / filename
            test_dir = path.parent / 'test'
            relative_path = path.relative_to(root_dir)
            if not test_dir.exists() or not test_dir.is_dir():
                violations.append((str(relative_path), "Missing sibling 'test' directory."))
                continue
            name_no_ext = path.stem
            preferred_test_name = f"{name_no_ext}_test.py"
            legacy_test_name = f"test_{name_no_ext}.py"
            preferred_path = test_dir / preferred_test_name
            legacy_path = test_dir / legacy_test_name
            if preferred_path.exists():
                continue # All good
            if legacy_path.exists():
                violations.append((str(relative_path), f"Found legacy test '{legacy_test_name}' in 'test'. Rename to '{preferred_test_name}'."))
                continue
            violations.append((str(relative_path), f"Missing test file in 'test'. Expected '{preferred_test_name}'."))
    return violations

def get_test_location_violations():
    root_dir = get_project_root()
    apps_dir = root_dir / 'apps'
    if not apps_dir.exists():
        return []
    violations = []
    SKIP_DIRS = {
        'node_modules', '.venv', 'custom-venv', 'dist', 'build', '.git', 
        '__pycache__', 'coverage', '.pytest_cache', '.mypy_cache'
    }
    SKIP_FILES = {'architecture_test.py'}
    for root, dirs, files in os.walk(apps_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d not in EXCLUDES]
        current_dir = Path(root)
        for filename in files:
            if filename in SKIP_FILES:
                continue
            if not filename.endswith('.py'):
                continue
            if not filename.endswith('_test.py') and not filename.startswith('test_'):
                continue
            file_path = current_dir / filename
            relative_path = file_path.relative_to(root_dir)
            if current_dir.name != 'test':
                 violations.append((str(relative_path), f"Test file found in '{current_dir.name}'. Must be in a 'test' directory."))
                 continue
            parent_dir = current_dir.parent
            if filename.endswith('_test.py'):
                prod_name = filename[:-8] + ".py"
            elif filename.startswith('test_'):
                prod_name = filename[5:]
                pass
            else:
                continue
            prod_file = parent_dir / prod_name
            if not prod_file.exists():
                prod_dir = parent_dir / prod_name[:-3] # remove .py
                if not prod_dir.exists() or not prod_dir.is_dir():
                    violations.append((str(relative_path), f"Corresponding production file '{prod_name}' not found in parent directory."))
    return violations

