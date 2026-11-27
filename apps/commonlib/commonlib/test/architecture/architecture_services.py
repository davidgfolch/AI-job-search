import ast
from pathlib import Path
from commonlib.test.architecture.architecture_util import get_project_root, iter_source_files

SERVICE_FILE_SUFFIXES = ('_service.py', 'Service.py')
REPOSITORY_FILE_SUFFIXES = ('_repository.py', 'Repository.py', 'repository.py')
REPOSITORY_LAYERS = frozenset({'repositories', 'sql'})


def _declared_layer(name):
    if name.endswith(SERVICE_FILE_SUFFIXES):
        return 'services'
    if name.endswith(REPOSITORY_FILE_SUFFIXES):
        return 'repositories'
    return None


def _in_layer(parts, layer):
    return layer in parts or (layer == 'repositories' and parts & REPOSITORY_LAYERS)


def get_misplaced_layer_symbols(root=None):
    """Find service/repository files and classes that sit outside their layer directory."""
    root = root or get_project_root()
    violations = []
    for path in iter_source_files(root / 'apps', extensions={'.py'}):
        parts = frozenset(path.parts)
        if 'test' in parts or 'tests' in parts or path.name in {'__init__.py', 'conftest.py'}:
            continue
        declared = _declared_layer(path.name)
        if declared and not _in_layer(parts, declared):
            violations.append((path, path.name, declared))
        try:
            tree = ast.parse(Path(path).read_text(encoding='utf-8'))
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name.endswith('Service') and not _in_layer(parts, 'services'):
                violations.append((path, node.name, 'services'))
            elif node.name.endswith('Repository') and not _in_layer(parts, 'repositories'):
                violations.append((path, node.name, 'repositories'))
    return violations
