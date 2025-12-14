
import pytest
import warnings
from architecture_util import *
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
        [('services', "Layer check: API file {rel_path} does not import any Service.")],
        [('repositories', "Layer violation: API file {rel_path} imports Repository layer directly.")],
        {'__init__.py', 'main.py'}),
    ('services',
        [('repositories', "Layer check: Service file {rel_path} does not import any Repository.")],
        [('api', "Layer violation: Service file {rel_path} imports API layer (circular dependency risk).")],
        None),
    ('repositories',
        [],
        [('services', "Layer violation: Repository file {rel_path} imports Service layer."),
        ('api', "Layer violation: Repository file {rel_path} imports API layer.")],
        None),
])
def test_backend_layered_architecture(layer_name, required_deps, forbidden_deps, ignore_files):
    root_dir = get_project_root()
    backend_dir = root_dir / 'apps' / 'backend'
    if not backend_dir.exists():
        return # Skip if backend directory doesn't exist
    check_layer(backend_dir / layer_name, root_dir,
        required_deps=required_deps,
        forbidden_deps=forbidden_deps,
        ignore_files=ignore_files)
