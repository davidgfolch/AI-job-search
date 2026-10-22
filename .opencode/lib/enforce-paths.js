// Path classification for the test-enforce guardrail.
//
// Decides whether a changed file requires the centralized test suite and which
// module it belongs to. Mirrored by .claude/hooks/lib/enforce_paths.py.
import { fileURLToPath } from "node:url";

// Directories that never hold runnable code for the suites.
const IGNORED_DIRS = new Set([
  ".git", ".codegraph", "node_modules", ".venv", "venv", "dist", "build", "coverage",
  "__pycache__", ".pytest_cache", ".ruff_cache", ".next", ".vite", ".claude",
  ".opencode", ".github", "e2e-artifacts", "test-results", "playwright-report",
]);
const DOC_SUFFIXES = [".md", ".mdx", ".txt", ".rst"];
const ASSET_SUFFIXES = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".woff", ".woff2", ".ttf", ".eot", ".pdf", ".mp4", ".webm", ".zip"];
// Scripts under scripts/ that the unit/e2e suites never exercise.
const NON_TEST_SCRIPTS = new Set([
  "install.sh", "install.bat", "uninstall.sh", "uninstall.bat",
  "test-sandbox.sh", "test-sandbox.bat", "nvidia-linux-restart.sh", "runMysql.sh",
  "lint.sh", "lint.bat",
]);
// Manifests whose change can break any module's suite.
const GLOBAL_MANIFESTS = new Set(["pyproject.toml", "package.json", "package-lock.json", "uv.lock", "poetry.lock"]);

export function toRoot(value) {
  if (!value) return process.cwd();
  if (typeof value === "string") return value;
  if (typeof URL !== "undefined" && value instanceof URL) return fileURLToPath(value);
  if (typeof value.pathname === "string") return value.pathname;
  return String(value);
}

export function relativize(filePath, root) {
  if (!filePath) return "";
  const p = filePath.replace(/\\/g, "/");
  const base = root ? root.replace(/\\/g, "/").replace(/\/+$/, "") : "";
  if (base && p.startsWith(base + "/")) return p.slice(base.length + 1);
  const marker = p.lastIndexOf("/apps/");
  if (marker >= 0) return p.slice(marker + 1);
  return p.replace(/^\/+/, "");
}

// Returns { modules: [...], global: bool } when the path requires the suites,
// or null when it does not (documentation, CI, coverage gates, agent tooling).
export function classify(relPath) {
  if (!relPath) return null;
  const rel = relPath.replace(/\\/g, "/").replace(/^\.\//, "");
  const segments = rel.split("/").filter(Boolean);
  if (!segments.length) return null;
  if (segments[0].toLowerCase() === "data") return null;
  if (segments.some((s) => IGNORED_DIRS.has(s.toLowerCase()))) return null;
  const base = segments[segments.length - 1].toLowerCase();
  const dot = base.lastIndexOf(".");
  const suffix = dot >= 0 ? base.slice(dot) : "";
  if (DOC_SUFFIXES.includes(suffix) || ASSET_SUFFIXES.includes(suffix)) return null;
  const moduleMatch = rel.match(/^apps\/([^/]+)\//i);
  if (moduleMatch) return { modules: [moduleMatch[1]], global: false };
  if (base.startsWith(".env")) return { modules: [], global: true };
  if (/^test[.][a-z]+$/.test(base)) return { modules: [], global: true };
  if (GLOBAL_MANIFESTS.has(base)) return { modules: [], global: true };
  if (segments[0].toLowerCase() === "scripts") {
    if (NON_TEST_SCRIPTS.has(base)) return null;
    return { modules: [], global: true };
  }
  return null;
}
