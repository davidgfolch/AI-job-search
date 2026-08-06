import path from 'path';
import type { CoverageReportOptions } from 'monocart-coverage-reports';

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
};
