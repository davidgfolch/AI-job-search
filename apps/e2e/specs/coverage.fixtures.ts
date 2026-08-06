import { CoverageReport } from 'monocart-coverage-reports';
import { test as base, expect, type Page } from '@playwright/test';
import { coverageOptions } from '../coverage.config';

/**
 * Specs must import `test`/`expect` from here instead of `@playwright/test`
 * so every test feeds Chromium's V8 coverage into monocart's shared cache.
 * V8 coverage via CDP is Chromium-only, so other browsers collect nothing.
 */
export const test = base.extend({
  page: async ({ page, browserName }, use) => {
    const collect = browserName === 'chromium';
    if (collect) {
      await page.coverage.startJSCoverage({ resetOnNavigation: false });
    }

    await use(page);

    if (collect) {
      try {
        const coverage = await page.coverage.stopJSCoverage();
        const report = new CoverageReport(coverageOptions);
        await report.add(coverage);
      } catch {
        // never fail a test over coverage collection
      }
    }
  },
});

export { expect, type Page };
