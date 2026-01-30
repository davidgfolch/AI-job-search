
import pytest
import warnings
from .architecture_util import *
from commonlib.terminalColor import YELLOW, RED, ORANGE, RESET

def test_files_exceed_200_lines():
    if files := getLongFiles():
        files.sort(key=lambda x: x[1], reverse=True)
        
        def format_line(f):
            path, lines = f
            if lines >= 300:
                color = RED
            elif lines >= 250:
                color = ORANGE
            else:
                color = YELLOW
            return f"{color}{path}: {lines} lines{RESET}"
            
        message = "\nFound files with more than 200 lines:\n" + "\n".join(format_line(f) for f in files)
        warnings.warn(UserWarning(message))

@pytest.mark.parametrize("layer_name, required_deps, forbidden_deps, ignore_files", [
    ('api',
        [('services', "Missing Service layer import.")],
        [('repositories', "Direct Repository layer import (skip Service layer).")],
        {'__init__.py', 'main.py'}),
    ('services',
        [],
        [('api', "Imports API layer (circular dependency risk)."),
         ('commonlib.mysqlUtil', "Direct Database Access (should use Repository).")],
        None),
    ('repositories',
        [],
        [('services', "Imports Service layer (circular dependency risk)."),
        ('api', "Imports API layer (circular dependency risk).")],
        None),
])
def test_backend_layered_architecture(layer_name, required_deps, forbidden_deps, ignore_files):
    root_dir = get_project_root()
    backend_dir = root_dir / 'apps' / 'backend'
    if not backend_dir.exists():
        return # Skip if backend directory doesn't exist
    error_msg = check_layer(backend_dir / layer_name, root_dir,
        required_deps=required_deps,
        forbidden_deps=forbidden_deps,
        ignore_files=ignore_files)
    if error_msg:
        pytest.fail(error_msg)

def test_sibling_test_folder_exists():
    violations = get_files_without_sibling_test()
    if violations:
        message = ""
        # Group by type of violation for cleaner output or just list them
        # Sorting by path
        violations.sort(key=lambda x: x[0])
        
        message += f"\n{YELLOW}Found files missing sibling tests (or using legacy naming):{RESET}\n"
        for path, reason in violations:
             message += f"{YELLOW}{path}{RESET}: {RED}{reason}{RESET}\n"
             
        print(message)
        pytest.fail(message)
