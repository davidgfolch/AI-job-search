
import os
from pathlib import Path
from commonlib.test.architecture.architecture_util import get_project_root, EXCLUDES

def get_test_naming_violations():
    root_dir = get_project_root()
    apps_dir = root_dir / 'apps'
    
    if not apps_dir.exists():
        return []

    violations = []
    
    # Directories to skip
    SKIP_DIRS = {
        'node_modules', '.venv', 'custom-venv', 'dist', 'build', '.git', 
        '__pycache__', 'coverage', '.pytest_cache'
    }

    for root, dirs, files in os.walk(apps_dir):
        # Filter directories inplace
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d not in EXCLUDES]
        
        # We only care about checking files INSIDE a 'test' directory
        if Path(root).name != 'test':
            continue

        for filename in files:
            if not filename.endswith('.py'):
                continue
            
            if filename == '__init__.py' or filename == 'conftest.py':
                continue

            # Rule 1: Test files must follow pattern *_test.py
            # Rule 2: Non-test files (helpers) must NOT contain "test" in name (case insensitive)
            
            lower_name = filename.lower()
            
            is_test_file = filename.endswith('_test.py')
            
            # Check for forbidden test patterns (e.g. test_*.py, Test*.py)
            # If it's not *_test.py, it should NOT look like a test file
            if not is_test_file:
                 # Check if it starts with test_ or Test (common pytest discovery patterns)
                 # or if the user simply wants NO "test" in the name for helpers.
                 
                 # "All non test files in test folders utils helpers should not contain test in name."
                 if 'test' in lower_name:
                     violations.append((
                         str(Path(root) / filename), 
                         f"Invalid file name in test folder. Test files must end in '_test.py'. Helper files must not contain 'test'. Found '{filename}'."
                     ))
                     
            # Implicitly, if it IS *_test.py, it is valid unless it violates something else?
            # The prompt says: "check all test files follow this pattern *_test.py, forbidden test_*.py or any other test combination in name."
            # So *_test.py is the ONLY allowed pattern for files containing "test".
            
            if is_test_file:
                continue
            
            if 'test' in lower_name:
                 violations.append((
                     str(Path(root) / filename), 
                     f"Invalid file name in test folder. Test files must end in '_test.py'. Helper files must not contain 'test'. Found '{filename}'."
                 ))
                 
    return violations
