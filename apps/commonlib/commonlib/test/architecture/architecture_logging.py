import ast
from pathlib import Path

from commonlib.test.architecture.architecture_util import get_project_root, EXCLUDES

LOG_METHODS = {"debug", "info", "warn", "warning", "error", "exception", "critical"}
CONSOLE_FIELDS = ("console", "end")

PRINT_ALLOWLIST = {
    # Presentational UI helpers: progress lines, tables, banners, countdown
    # spinners, interactive browser prompts. Every other print() must become a
    # structured event via commonlib.observability (see READMEs/README_DEVELOPMENT.md).
    "apps/aiEnrich3/src/aiEnrich3/main.py",
    "apps/aiEnrichSkill/src/aiEnrichSkill/services/enrichment_service.py",
    "apps/commonlib/commonlib/ai_helpers.py",
    "apps/commonlib/commonlib/decorator/retry.py",
    "apps/commonlib/commonlib/sqlUtil.py",
    "apps/commonlib/commonlib/stopWatch.py",
    "apps/commonlib/commonlib/sync/mysql_sync.py",
    "apps/commonlib/commonlib/terminalColor.py",
    "apps/commonlib/commonlib/terminalUtil.py",
    "apps/scrapper/scrapper/core/baseScrapper.py",
    "apps/scrapper/scrapper/core/scrapper_scheduler.py",
    "apps/scrapper/scrapper/executor/GlassdoorExecutor.py",
    "apps/scrapper/scrapper/executor/IndeedExecutor.py",
    "apps/scrapper/scrapper/executor/IndeedScraplingExecutor.py",
    "apps/scrapper/scrapper/executor/InfojobsExecutor.py",
    "apps/scrapper/scrapper/executor/LinkedinExecutor.py",
    "apps/scrapper/scrapper/executor/TecnoempleoExecutor.py",
    "apps/scrapper/scrapper/navigator/glassdoorNavigator.py",
    "apps/scrapper/scrapper/navigator/indeedNavigator.py",
    "apps/scrapper/scrapper/navigator/infojobsNavigator.py",
    "apps/scrapper/scrapper/navigator/linkedinNavigator.py",
    "apps/scrapper/scrapper/navigator/tecnoempleoNavigator.py",
    "apps/scrapper/scrapper/services/selenium/element_service.py",
    "apps/scrapper/scrapper/util/terminalTableUtil.py",
}

def get_print_violations(root=None):
    root = Path(root).resolve() if root else get_project_root()
    apps_dir = root / "apps"
    violations = []
    for path in sorted(apps_dir.rglob("*.py")):
        if any(ex in path.parts for ex in EXCLUDES):
            continue
        if any(part in {"test", "tests"} for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        if rel in PRINT_ALLOWLIST:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                segment = ast.get_source_segment(path.read_text(encoding="utf-8", errors="ignore"), node)
                snippet = " ".join(segment.strip().split())
                violations.append(f"{rel}:{node.lineno}: print({snippet[:120]})")
    return violations


def _is_log_call(node) -> bool:
    """True for `logger.info(...)`-style calls, including `self.logger.info(...)`."""
    if not isinstance(node, ast.Call):
        return False
    if not isinstance(node.func, ast.Attribute) or node.func.attr not in LOG_METHODS:
        return False
    target = node.func.value
    if isinstance(target, ast.Name):
        return "log" in target.id.lower()
    if isinstance(target, ast.Attribute):
        return "log" in target.attr.lower()
    return False


def get_console_violations(root=None):
    """Report logger calls that break the `console=` contract of commonlib.observability.

    The JSONL is queried by event name, so a call must keep a literal `domain.action`
    even when it prints human text. `end=` only means something next to `console=`, and
    it must be a literal so a progress prefix stays predictable.
    """
    root = Path(root).resolve() if root else get_project_root()
    apps_dir = root / "apps"
    violations = []
    for path in sorted(apps_dir.rglob("*.py")):
        if any(ex in path.parts for ex in EXCLUDES):
            continue
        if any(part in {"test", "tests"} for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not _is_log_call(node):
                continue
            keywords = {kw.arg for kw in node.keywords if kw.arg}
            event = node.args[0] if node.args else None
            if isinstance(event, (ast.JoinedStr, ast.BinOp, ast.Call)):
                violations.append(f"{rel}:{node.lineno}: event name must be a literal, not {type(event).__name__}")
            if "end" in keywords and "console" not in keywords:
                violations.append(f"{rel}:{node.lineno}: end= without console= does nothing")
            for kw in node.keywords:
                if kw.arg == "end" and not (isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str)):
                    violations.append(f"{rel}:{node.lineno}: end= must be a string literal")
    return violations