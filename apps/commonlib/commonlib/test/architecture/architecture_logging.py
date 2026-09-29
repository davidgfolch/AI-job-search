import ast
from pathlib import Path

from commonlib.test.architecture.architecture_util import get_project_root, EXCLUDES

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
    "apps/scrapper/scrapper/executor/InfojobsExecutor.py",
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