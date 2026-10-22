"""Path classification for the test-enforce guardrail.

Decides whether a changed file requires the centralized test suite and which
module it belongs to. Mirrored by .opencode/lib/enforce-paths.js.
"""
import re

# Directories that never hold runnable code for the suites.
IGNORED_DIRS = {
    ".git", ".codegraph", "node_modules", ".venv", "venv", "dist", "build", "coverage",
    "__pycache__", ".pytest_cache", ".ruff_cache", ".next", ".vite", ".claude",
    ".opencode", ".github", "e2e-artifacts", "test-results", "playwright-report",
}
DOC_SUFFIXES = (".md", ".mdx", ".txt", ".rst")
ASSET_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".woff", ".woff2", ".ttf", ".eot", ".pdf", ".mp4", ".webm", ".zip")
# Scripts under scripts/ that the unit/e2e suites never exercise.
NON_TEST_SCRIPTS = {
    "install.sh", "install.bat", "uninstall.sh", "uninstall.bat",
    "test-sandbox.sh", "test-sandbox.bat", "nvidia-linux-restart.sh", "runMysql.sh",
    "lint.sh", "lint.bat",
}
# Manifests whose change can break any module's suite.
GLOBAL_MANIFESTS = {"pyproject.toml", "package.json", "package-lock.json", "uv.lock", "poetry.lock"}
MODULE_PATH = re.compile(r"^apps/([^/]+)/", re.IGNORECASE)
TEST_BASENAME = re.compile(r"^test[.][a-z]+$")


def relativize(file_path: str, root: str) -> str:
    if not file_path:
        return ""
    path = file_path.replace("\\", "/")
    base = root.replace("\\", "/").rstrip("/")
    if base and path.startswith(base + "/"):
        return path[len(base) + 1:]
    marker = path.rfind("/apps/")
    if marker >= 0:
        return path[marker + 1:]
    return path.lstrip("/")


def classify(rel_path: str):
    """Return (modules, is_global) when the path requires the suites, else None."""
    if not rel_path:
        return None
    rel = rel_path.replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    segments = [s for s in rel.split("/") if s]
    if not segments:
        return None
    if segments[0].lower() == "data":
        return None
    if any(s.lower() in IGNORED_DIRS for s in segments):
        return None
    base = segments[-1].lower()
    suffix = base[base.rfind("."):] if "." in base else ""
    if suffix in DOC_SUFFIXES or suffix in ASSET_SUFFIXES:
        return None
    module_match = MODULE_PATH.match(rel)
    if module_match:
        return ([module_match.group(1)], False)
    if base.startswith(".env"):
        return ([], True)
    if TEST_BASENAME.match(base):
        return ([], True)
    if base in GLOBAL_MANIFESTS:
        return ([], True)
    if segments[0].lower() == "scripts":
        if base in NON_TEST_SCRIPTS:
            return None
        return ([], True)
    return None
