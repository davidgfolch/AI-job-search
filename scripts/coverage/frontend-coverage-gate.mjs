/**
 * Frontend coverage gate: enforces a 90% floor on the union of the web unit
 * (vitest) and e2e (Playwright + monocart) coverage of the same frontend.
 *
 * Both suites measure the same source tree with different tools: vitest covers
 * components through jsdom, monocart covers them through a real browser.
 * Neither number alone is meaningful -- a lazily-routed page is invisible to the
 * unit run and barely touched by e2e -- so the floor applies to the union.
 *
 * Union rule: per file, `total` and `covered` are the max of the two reports.
 * Both tools count the same source lines, so max is the standard approximation
 * for a union of covered-line sets (the exact union is not derivable from counts
 * alone, because the two suites may well cover the same line).
 *
 * Usage: node scripts/coverage/frontend-coverage-gate.mjs [--min 90]
 * Env:   WEB_UNIT_COVERAGE / E2E_COVERAGE / FRONTEND_COVERAGE_OUT override paths.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const MIN = Number(process.argv.includes('--min') ? process.argv[process.argv.indexOf('--min') + 1] : 90);
const GATED = ['lines', 'statements'];
const METRICS = ['lines', 'statements', 'functions', 'branches'];

const WEB_SUMMARY = process.env.WEB_UNIT_COVERAGE || path.join(ROOT, 'apps/web/coverage/coverage-summary.json');
const E2E_SUMMARY = process.env.E2E_COVERAGE || path.join(ROOT, 'apps/e2e/coverage/coverage-summary.json');
const OUT_SUMMARY = process.env.FRONTEND_COVERAGE_OUT || path.join(ROOT, 'apps/e2e/coverage/coverage-frontend-summary.json');

/**
 * Keys differ between the two tools: vitest writes absolute paths
 * (`C:/.../apps/web/src/App.tsx`) and monocart writes entry-URL relative ones
 * (`src/App.tsx`). Both are canonicalised to `apps/web/src/...` so a file measured
 * by both suites merges into one entry instead of being counted twice.
 */
const keyOf = rawKey => {
  const norm = rawKey.replace(/\\/g, '/');
  const treeAt = norm.lastIndexOf('apps/web/');
  if (treeAt >= 0) return norm.slice(treeAt);
  const srcAt = norm.indexOf('/src/');
  if (srcAt >= 0) return `apps/web${norm.slice(srcAt)}`;
  const relative = norm.replace(/^\.\//, '');
  if (relative.startsWith('src/')) return `apps/web/${relative}`;
  return norm;
};

function readSummary(file, label) {
  if (!fs.existsSync(file)) {
    throw new Error(
      `Missing ${label} coverage summary: ${path.relative(ROOT, file)}\n` +
        (label === 'web unit'
          ? 'Run it from apps/web with: npm test -- run --coverage'
          : 'Run it from apps/e2e with: npm test (Playwright global teardown writes the report)')
    );
  }
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

/** Re-key one report by canonical path, keeping the max of any duplicate entry. */
function byKey(report) {
  const map = new Map();
  for (const [rawKey, value] of Object.entries(report)) {
    if (rawKey === 'total' || !value) continue;
    const key = keyOf(rawKey);
    const block = map.get(key) ?? {};
    for (const metric of METRICS) {
      const entry = value[metric];
      if (!entry) continue;
      const total = Math.max(block[metric]?.total ?? 0, entry.total ?? 0);
      const covered = Math.min(Math.max(block[metric]?.covered ?? 0, entry.covered ?? 0), total);
      block[metric] = { total, covered, skipped: 0, pct: Number(((covered / total) * 100).toFixed(2)) };
    }
    map.set(key, block);
  }
  return map;
}

const web = byKey(readSummary(WEB_SUMMARY, 'web unit'));
const e2e = byKey(readSummary(E2E_SUMMARY, 'e2e'));

/**
 * A file count mismatch means the two configs stopped sharing one denominator --
 * the failure mode that made e2e report only the pages it happened to load.
 */
const drift = [];
for (const key of web.keys()) if (!e2e.has(key)) drift.push(`only in web unit: ${key}`);
for (const key of e2e.keys()) if (!web.has(key)) drift.push(`only in e2e: ${key}`);

const files = new Set([...web.keys(), ...e2e.keys()]);
const summary = {};
const totals = Object.fromEntries(METRICS.map(metric => [metric, { total: 0, covered: 0, skipped: 0 }]));

for (const key of files) {
  const webFile = web.get(key);
  const e2eFile = e2e.get(key);
  const block = {};
  for (const metric of METRICS) {
    const total = Math.max(webFile?.[metric]?.total ?? 0, e2eFile?.[metric]?.total ?? 0);
    if (!total) continue;
    const covered = Math.min(Math.max(webFile?.[metric]?.covered ?? 0, e2eFile?.[metric]?.covered ?? 0), total);
    block[metric] = { total, covered, skipped: 0, pct: Number(((covered / total) * 100).toFixed(2)) };
    totals[metric].total += total;
    totals[metric].covered += covered;
  }
  if (Object.keys(block).length) summary[key] = block;
}
for (const metric of METRICS) {
  totals[metric].pct = totals[metric].total ? Number(((totals[metric].covered / totals[metric].total) * 100).toFixed(2)) : 100;
}
summary.total = totals;

fs.mkdirSync(path.dirname(OUT_SUMMARY), { recursive: true });
fs.writeFileSync(OUT_SUMMARY, JSON.stringify(summary, null, 2));
console.log(`Frontend (web unit + e2e) coverage written to ${path.relative(ROOT, OUT_SUMMARY)}\n`);

let failed = false;
if (drift.length) {
  failed = true;
  console.error(`\nDenominator drift: the two suites measured ${web.size} and ${e2e.size} files.`);
  for (const entry of drift.slice(0, 20)) console.error(`  ${entry}`);
  if (drift.length > 20) console.error(`  ...and ${drift.length - 20} more`);
  console.error('Both configs must include every production file under apps/web/src.\n');
}
for (const metric of METRICS) {
  const { covered, total, pct } = totals[metric];
  const gate = GATED.includes(metric);
  if (gate && pct < MIN) failed = true;
  console.log(`  ${metric.padEnd(11)} ${String(covered).padStart(5)}/${String(total).padEnd(5)} = ${String(pct).padStart(6)}%  ${gate ? `min ${MIN}` : 'reported only'}`);
}

const worst = Object.entries(summary)
  .filter(([key]) => key !== 'total')
  .map(([file, value]) => ({ file, missed: GATED.reduce((sum, metric) => sum + (value[metric]?.total ?? 0) - (value[metric]?.covered ?? 0), 0) }))
  .filter(entry => entry.missed > 0)
  .sort((a, b) => b.missed - a.missed)
  .slice(0, 20);
if (worst.length) {
  console.log('\nLeast covered files (missing lines + statements):');
  for (const { file, missed } of worst) console.log(`  ${String(missed).padStart(4)}  ${file}`);
}

if (failed) {
  console.error(`\nFAIL: frontend coverage below ${MIN}% on ${GATED.join(' / ')}.`);
  process.exit(1);
}
console.log(`\nPASS: frontend coverage at or above ${MIN}% on ${GATED.join(' / ')}.`);
