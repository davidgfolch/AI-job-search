
import os
from pathlib import Path
from commonlib.test.architecture.architecture_util import get_project_root, EXCLUDES

def get_files_without_sibling_test():
    root_dir = get_project_root()
    apps_dir = root_dir / 'apps'
    
    if not apps_dir.exists():
        return []

    violations = []

    # Files to likely ignore
    IGNORED_FILES = {'__init__.py', 'conftest.py', 'setup.py', 'main.py'}
    
    # Directories to skip
    SKIP_DIRS = {
        'node_modules', '.venv', 'custom-venv', 'dist', 'build', '.git', 
        '__pycache__', 'coverage', '.pytest_cache', 'test'
    }
    
    INVALID_TEST_DIRS = {'__test__', 'tests', '__tests__'}

    for root, dirs, files in os.walk(apps_dir):
        # Check for invalid directory names
        for d in dirs:
            if d in INVALID_TEST_DIRS:
                # Check if it contains python files to confirm it's a python test folder
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

        # Filter directories inplace
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d not in EXCLUDES and d not in INVALID_TEST_DIRS]
        
        # If we are inside a test dir (shouldn't happen with filter above), continue
        if Path(root).name == 'test':
            continue

        for filename in files:
            if not filename.endswith('.py'):
                continue
            
            if filename in IGNORED_FILES:
                continue

            # Skip test files themselves if they happen to be outside test but follow pattern
            if filename.startswith('test_') or filename.endswith('_test.py'):
                continue
            
            # Additional check: Skip if file itself is obviously a script often without tests? 
            # (Assuming current logic is fine)
            
            path = Path(root) / filename
            
            # Look for 'test' sibling
            test_dir = path.parent / 'test'
            
            relative_path = path.relative_to(root_dir)
            
            if not test_dir.exists() or not test_dir.is_dir():
                violations.append((str(relative_path), "Missing sibling 'test' directory."))
                continue
            
            # Check for test file variants
            # correct: [name]_test.py
            # legacy: test_[name].py
            
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
