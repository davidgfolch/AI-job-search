import { CoverageReport } from 'monocart-coverage-reports';
import { test as base, expect, type Page } from '@playwright/test';
import { coverageOptions } from '../coverage.config';
import { setupApiSafetyNet } from './common.helpers';

/**
 * Specs must import `test`/`expect` from here instead of `@playwright/test`
 * so every test feeds Chromium's V8 coverage into monocart's shared cache.
 * V8 coverage via CDP is Chromium-only, so other browsers collect nothing.
 *
 * The auto fixture registers the API safety net first (before each spec's own
 * routes), so explicit mocks win while any unmocked write fails loudly instead
 * of silently reaching the live backend and its database.
 */
export const test = base.extend<{ apiWriteGuard: void }>({
  apiWriteGuard: [async ({ page }, use) => {
    await setupApiSafetyNet(page);
    await use();
  }, { auto: true }],
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
