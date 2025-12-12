
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
    # Assuming this test is in packages/commonlib/test
    current_dir = Path(__file__).resolve().parent
    return current_dir.parent.parent.parent

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

def _validate_dependencies(deps, imports, rel_path, should_exist):
    for layer, msg in deps:
        has_dep = any(
            imp.startswith(layer) or imp.startswith(f'apps.backend.{layer}') 
            for imp in imports
        )
        if should_exist and not has_dep:
            warnings.warn(UserWarning(msg.format(rel_path=rel_path)))
        elif not should_exist and has_dep:
            warnings.warn(UserWarning(msg.format(rel_path=rel_path)))

def check_layer(working_dir, root_dir, required_deps=None, forbidden_deps=None, ignore_files=None):
    if not working_dir.exists():
        return
    if ignore_files is None:
        ignore_files = {'__init__.py'}
    if required_deps is None:
        required_deps = []
    if forbidden_deps is None:
        forbidden_deps = []
    for file_path in working_dir.glob('**/*.py'):
        if file_path.name in ignore_files:
            continue
        imports = get_file_imports(file_path)
        rel_path = file_path.relative_to(root_dir)
        _validate_dependencies(required_deps, imports, rel_path, should_exist=True)
        _validate_dependencies(forbidden_deps, imports, rel_path, should_exist=False)
