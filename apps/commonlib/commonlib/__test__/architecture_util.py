import os
import warnings
import ast
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
    return current_dir.parent.parent.parent.parent

def count_lines(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0

def getLongFiles():
    root_dir = get_project_root()
    result = []
    assert (root_dir / 'apps').exists(), f"Could not find apps dir at {root_dir}"
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDES]
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix not in EXTENSIONS:
                continue
            if (lines := count_lines(file_path)) > 200:
                result.append((str(file_path.relative_to(root_dir)), lines))
    return result

def get_file_imports(file_path):
    result = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    result.add(node.module)
    except Exception: # If we can't parse the file, just ignore it
        pass
    return result

def _validate_dependencies(deps, imports, should_exist):
    invalid = []
    for layer, msg in deps:
        has_dep = any(
            imp.startswith(layer) or imp.startswith(f'apps.backend.{layer}') 
            for imp in imports
        )
        if should_exist and not has_dep:
            invalid.append(msg)
        elif not should_exist and has_dep:
            invalid.append(msg)
    return invalid

def check_layer(working_dir, root_dir, required_deps=None, forbidden_deps=None, ignore_files=None):
    if not working_dir.exists():
        return
    if ignore_files is None:
        ignore_files = {'__init__.py'}
    if required_deps is None:
        required_deps = []
    if forbidden_deps is None:
        forbidden_deps = []
    file_violations = {}
    for file_path in working_dir.glob('**/*.py'):
        if file_path.name in ignore_files:
            continue

        if '__test__' in str(file_path):
            continue
        imports = get_file_imports(file_path)
        
        current_violations = []
        current_violations += _validate_dependencies(required_deps, imports, should_exist=True)
        current_violations += _validate_dependencies(forbidden_deps, imports, should_exist=False)
        
        if current_violations:
            rel_path = file_path.relative_to(root_dir)
            file_violations[str(rel_path)] = current_violations

    if file_violations:
        from commonlib.terminalColor import RED, RESET, YELLOW
        messages = [f"\n{YELLOW}Found architectural violations:{RESET}"]
        
        for path, violations in sorted(file_violations.items()):
            messages.append(f"{YELLOW}{path}{RESET}")
            for v in violations:
                messages.append(f"  - {RED}{v}{RESET}")
            messages.append("") # Empty line between files
            
        warnings.warn(UserWarning('\n'.join(messages)))

def get_files_without_sibling_test():
    root_dir = get_project_root()
    # We want to check 'apps' largely, but let's stick to what getLongFiles does or similar,
    # or just walk safely.
    apps_dir = root_dir / 'apps'
    
    if not apps_dir.exists():
        return []

    violations = []

    # Files to likely ignore
    IGNORED_FILES = {'__init__.py', 'conftest.py', 'setup.py', 'main.py'}
    
    # Directories to skip
    SKIP_DIRS = {
        'node_modules', '.venv', 'custom-venv', 'dist', 'build', '.git', 
        '__pycache__', 'coverage', '.pytest_cache', 'test', 'tests'
    }

    for root, dirs, files in os.walk(apps_dir):
        # Filter directories inplace
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d not in EXCLUDES]
        
        # If we are inside a __test__ dir, we probably don't need to check for tests there
        # depending on if we recursively allow tests of tests. usually no.
        if Path(root).name == '__test__':
            continue

        for filename in files:
            if not filename.endswith('.py'):
                continue
            
            if filename in IGNORED_FILES:
                continue

            # Skip test files themselves if they happen to be outside __test__ but follow pattern
            # (though the goal IS to enforce __test__ so we should flag them if they are code?)
            # Usually simple heuristic: if it looks like a test, skip it.
            if filename.startswith('test_') or filename.endswith('_test.py'):
                continue
            
            path = Path(root) / filename
            
            # Look for __test__ sibling
            test_dir = path.parent / '__test__'
            
            relative_path = path.relative_to(root_dir)
            
            if not test_dir.exists() or not test_dir.is_dir():
                violations.append((str(relative_path), "Missing sibling '__test__' directory."))
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
                violations.append((str(relative_path), f"Found legacy test '{legacy_test_name}'. Rename to '{preferred_test_name}'."))
                continue
                
            violations.append((str(relative_path), f"Missing test file in '__test__'. Expected '{preferred_test_name}'."))

    return violations
