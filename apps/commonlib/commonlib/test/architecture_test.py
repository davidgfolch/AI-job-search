
import pytest
import warnings
from commonlib.test.architecture.architecture_util import get_project_root
from commonlib.test.architecture.architecture_metrics import getLongFiles
from commonlib.test.architecture.architecture_layers import check_layer
from commonlib.test.architecture.architecture_layer_rules import LAYER_RULES, discover_layer_keys
from commonlib.test.architecture.architecture_structure import get_files_without_sibling_test, get_test_location_violations
from commonlib.test.architecture.architecture_naming import get_test_naming_violations
from commonlib.test.architecture.architecture_logging import get_console_violations, get_print_violations
from commonlib.test.architecture.architecture_scripts import get_non_executable_scripts
from commonlib.test.architecture.architecture_services import get_misplaced_layer_symbols
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
        warnings.warn(UserWarning(message), stacklevel=2)

def test_shell_scripts_are_executable():
    violations = get_non_executable_scripts()
    if violations:
        message = f"{YELLOW}Shell scripts stored without the executable bit (fresh clones cannot run them):{RESET}\n"
        for path in violations:
            message += f"{RED}{path}{RESET}\n"
        message += f"{YELLOW}Fix with: git update-index --chmod=+x <path>{RESET}"
        pytest.fail(message)

@pytest.mark.parametrize("rule", LAYER_RULES, ids=lambda rule: f"{rule.module}:{rule.layer}")
def test_layered_architecture(rule):
    root_dir = get_project_root()
    error_msg = check_layer(rule.path(root_dir), root_dir, package=rule.package,
        required_deps=rule.required, forbidden_deps=rule.forbidden, ignore_files=rule.ignore_files,
        extra_files=rule.extra_files(root_dir))
    if error_msg:
        pytest.fail(error_msg)

def test_layer_rules_cover_all_modules():
    root_dir = get_project_root()
    discovered = discover_layer_keys(root_dir)
    defined = {rule.key for rule in LAYER_RULES}
    assert discovered <= defined, f"Layers without architecture rules: {sorted(discovered - defined)}"
    assert defined <= discovered, f"Rules for non-existent layers: {sorted(defined - discovered)}"

def test_service_and_repository_symbols_live_in_their_layers():
    violations = get_misplaced_layer_symbols()
    if violations:
        message = f"\n{YELLOW}Found service/repository symbols outside their layer directories:{RESET}\n"
        for path, symbol, layer in violations:
            message += f"{RED}{path.relative_to(get_project_root())}: {symbol} belongs in {layer}/{RESET}\n"
        pytest.fail(message)

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

def test_test_file_naming_conventions():
    violations = get_test_naming_violations()
    if violations:
        message = f"\n{YELLOW}Found test file naming violations:{RESET}\n"
        for path, reason in violations:
             message += f"{YELLOW}{path}{RESET}: {RED}{reason}{RESET}\n"
        print(message)
        pytest.fail(message)

def test_no_bare_print_in_source():
    violations = get_print_violations()
    if violations:
        message = f"\n{YELLOW}Found print() calls outside the presentational allowlist.{RESET}\n"
        message += f"{YELLOW}Convert them to structured events via commonlib.observability, or\n"
        message += f"justify the presentational output and add the file to PRINT_ALLOWLIST:{RESET}\n"
        for violation in violations:
            message += f"{RED}{violation}{RESET}\n"
        pytest.fail(message)

def test_console_field_contract():
    violations = get_console_violations()
    if violations:
        message = f"\n{YELLOW}Found logger calls that break the console= contract.{RESET}\n"
        message += f"{YELLOW}Keep a literal domain.action event name, pair end= with console=,\n"
        message += f"and pass a string literal as end= (see commonlib.console_render):{RESET}\n"
        for violation in violations:
            message += f"{RED}{violation}{RESET}\n"
        pytest.fail(message)

def test_module_field_is_rejected_on_log_calls(tmp_path):
    """`module` is stamped from the caller, so a call must not pass it as its own data."""
    app = tmp_path / "apps" / "fakeapp"
    app.mkdir(parents=True)
    (app / "worker.py").write_text(
        "from commonlib.observability import get_logger\n"
        "logger = get_logger('fakeapp.worker')\n"
        "logger.info('job.done', module='fakeapp.worker')\n",
        encoding="utf-8",
    )

    violations = get_console_violations(root=tmp_path)

    assert len(violations) == 1
    assert "module= is reserved" in violations[0]

def test_source_module_is_allowed_on_log_calls(tmp_path):
    """The reader of the stamped value is named `source_module`, so it is not rejected."""
    app = tmp_path / "apps" / "fakeapp"
    app.mkdir(parents=True)
    (app / "worker.py").write_text(
        "from commonlib.observability import get_logger\n"
        "logger = get_logger('fakeapp.worker')\n"
        "logger.info('job.done', source_module='fakeapp.worker')\n",
        encoding="utf-8",
    )

    assert get_console_violations(root=tmp_path) == []

def test_test_file_location_and_correspondence():
    violations = get_test_location_violations()
    if violations:
        message = f"\n{YELLOW}Found test file location/correspondence violations:{RESET}\n"
        for path, reason in violations:
             message += f"{YELLOW}{path}{RESET}: {RED}{reason}{RESET}\n"
        print(message)
        pytest.fail(message)
