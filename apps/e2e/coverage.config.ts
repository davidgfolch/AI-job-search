import path from 'path';
import type { CoverageReportOptions } from 'monocart-coverage-reports';

/**
 * Root of the measured app. Absolute on purpose: Playwright runs global setup
 * and teardown with cwd = apps/e2e, so a relative path would resolve against
 * the wrong root.
 */
const WEB_SRC_DIR = path.resolve(__dirname, '../web/src');

/** The only extensions that carry executable frontend code. */
const isSourceFile = (filePath: string) => /\.(ts|tsx)$/.test(filePath);

/**
 * Test code lives in `test/` folders. Keeping it out of the denominator is what
 * makes the number reflect production code, and it mirrors the `coverage.exclude`
 * list in apps/web/vite.config.ts so both feeds share one denominator.
 */
const isProductionFile = (filePath: string) =>
  isSourceFile(filePath) && !/(^|[\\/])test[\\/]/.test(filePath);

/**
 * Shared monocart-coverage-reports options used by the Playwright global
 * setup/teardown and the per-test fixture that feeds V8 coverage into the
 * shared on-disk cache.
 *
 * Vite dev source maps unpack each module to a bare basename, losing its
 * directory, so two adjustments map coverage back to the app's own sources:
 *   * entryFilter keeps only the app modules Vite serves under `/src/`, dropping
 *     pre-bundled dependencies (node_modules/.vite/deps/*), @vite/client and CSS.
 *   * sourcePath rebuilds the real path from the entry URL (info.distFile),
 *     which is 1:1 with its source.
 */
export const coverageOptions: CoverageReportOptions = {
  name: 'E2E Frontend Coverage',
  outputDir: path.resolve(__dirname, 'coverage'),
  reports: ['json-summary', 'console-summary'],
  entryFilter: entry => {
    const url = entry.url ?? '';
    if (!url.includes('/src/')) {
      return false;
    }
    return !/\.css(\?|$)|type=style|lang\.css/.test(url);
  },
  sourcePath: (filePath, info) => {
    const dist = (info.distFile ?? filePath).replace(/\\/g, '/');
    const match = dist.match(/src\/.+$/);
    return (match ? match[0] : filePath).replace(/[?].*$/, '');
  },
  /**
   * By default monocart only reports files a browser actually loaded, which
   * flatters the total: a lazily-routed page no spec visits simply disappears.
   * `all` adds every production source under web/src as empty coverage so the
   * denominator is the whole frontend.
   */
  all: {
    dir: WEB_SRC_DIR,
    filter: filePath => (isProductionFile(filePath) ? 'js' : false),
  },
  /**
   * Called with the source-map source path (`src/pages/...` or a relative
   * variant), not an absolute path, so this has to be a plain predicate: a
   * pattern-based filter would never match and drop every source.
   */
  sourceFilter: sourcePath => isProductionFile(sourcePath),
};
