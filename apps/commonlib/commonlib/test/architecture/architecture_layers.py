
import ast
from commonlib.terminalColor import RED, RESET, YELLOW

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

        # Ignore test folders for architecture violations (they can import whatever they need for mocking)
        # We check for 'test' in the parts of the path to be robust
        if 'test' in file_path.parts:
            continue
        imports = get_file_imports(file_path)
        
        current_violations = []
        current_violations += _validate_dependencies(required_deps, imports, should_exist=True)
        current_violations += _validate_dependencies(forbidden_deps, imports, should_exist=False)
        
        if current_violations:
            messages = [f"\n{YELLOW}Found architectural violations:{RESET}"]
            
            for path, violations in sorted(file_violations.items()):
                messages.append(f"{YELLOW}{path}{RESET}")
                for v in violations:
                    messages.append(f"  - {RED}{v}{RESET}")
                messages.append("") # Empty line between files
                
            # Wait, the logic above in original file accumulates messages but here I pasted inside the loop?
            # Let me check the original file content again to be sure I copied logic correctly.
            # In original:
            # if current_violations:
            #    file_violations[str(rel_path)] = current_violations
            # THEN after loop:
            # if file_violations:
            #    construct message
            
            rel_path = file_path.relative_to(root_dir)
            file_violations[str(rel_path)] = current_violations

    if file_violations:
        messages = [f"\n{YELLOW}Found architectural violations:{RESET}"]
        
        for path, violations in sorted(file_violations.items()):
            messages.append(f"{YELLOW}{path}{RESET}")
            for v in violations:
                messages.append(f"  - {RED}{v}{RESET}")
            messages.append("") # Empty line between files
            
        return '\n'.join(messages)
    return None
