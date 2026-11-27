
import ast
from commonlib.terminalColor import RED, RESET, YELLOW
from commonlib.test.architecture.architecture_util import iter_source_files

def get_file_imports(file_path):
    result = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                result.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    result.add(node.module)
                elif node.level: # from . import layer
                    result.update(alias.name for alias in node.names)
    except Exception: # If we can't parse the file, just ignore it
        pass
    return result

def _matches(imp, layer, package):
    prefixes = (layer, f'commonlib.{layer}', f'{package}.{layer}')
    return any(imp == prefix or imp.startswith(f'{prefix}.') for prefix in prefixes)

def _validate_dependencies(deps, imports, should_exist, package=None):
    invalid = []
    for layer, msg in deps:
        has_dep = any(_matches(imp, layer, package) for imp in imports)
        if has_dep != should_exist:
            invalid.append(msg)
    return invalid

def check_layer(working_dir, root_dir, required_deps=None, forbidden_deps=None, ignore_files=None, package=None, extra_files=()):
    if not working_dir.exists() and not extra_files:
        return
    if ignore_files is None:
        ignore_files = {'__init__.py'}
    if required_deps is None:
        required_deps = []
    if forbidden_deps is None:
        forbidden_deps = []
    files = list(extra_files)
    if working_dir.exists():
        files.extend(iter_source_files(working_dir, extensions={'.py'}))
    file_violations = {}
    for file_path in files:
        if file_path.name in ignore_files or 'test' in file_path.parts:
            continue
        imports = get_file_imports(file_path)
        violations = _validate_dependencies(required_deps, imports, should_exist=True, package=package)
        violations += _validate_dependencies(forbidden_deps, imports, should_exist=False, package=package)
        if violations:
            file_violations[str(file_path.relative_to(root_dir))] = violations
    if not file_violations:
        return None
    messages = [f"\n{YELLOW}Found architectural violations:{RESET}"]
    for path, violations in sorted(file_violations.items()):
        messages.append(f"{YELLOW}{path}{RESET}")
        messages.extend(f"  - {RED}{violation}{RESET}" for violation in violations)
        messages.append("")
    return '\n'.join(messages)
