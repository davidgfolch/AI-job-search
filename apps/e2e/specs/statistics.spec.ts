import { test, expect } from './coverage.fixtures';
import { Page } from '@playwright/test';
import { BASE_URL, setupPageLogging, setupAppBootstrapMocks } from './common.helpers';

const KEYWORD_STATS = {
    items: [
        { date: '2026-11-19', site: 'Linkedin', keyword: 'python', reported_total: 40, processed: 20, new: 18, duplicates: 2, duplicate_ids: '91,92' },
        { date: '2026-11-19', site: 'Linkedin', keyword: 'java', reported_total: 10, processed: 5, new: 5, duplicates: 0, duplicate_ids: '' },
        { date: '2026-11-19', site: 'Indeed', keyword: 'python', reported_total: 5, processed: 5, new: 1, duplicates: 4, duplicate_ids: '7,8,9,10' },
        { date: '2026-11-19', site: 'Glassdoor', keyword: 'python', reported_total: 99, processed: 99, new: 50, duplicates: 49, duplicate_ids: '77' },
    ],
    truncated: false,
};

async function setupStatisticsMocks(page: Page) {
    await setupAppBootstrapMocks(page);
    await page.route(/.*\/api\/statistics\/.*/, async route => {
        const payload = route.request().url().includes('/keywords') ? KEYWORD_STATS : [];
        await route.fulfill({ contentType: 'application/json', json: payload });
    });
}

test.describe('Statistics E2E', () => {
    test.beforeEach(async ({ page }) => {
        setupPageLogging(page);
        await setupStatisticsMocks(page);
    });

    test('shows keyword lines for the default site and filters by site', async ({ page }) => {
        await page.goto(`${BASE_URL}/statistics`);
        await expect(page.getByText('Keyword totals & duplicates by date')).toBeVisible();
        await expect(page.locator('.keyword-chart .recharts-line')).toHaveCount(2);
        await expect(page.locator('.keyword-chart .recharts-bar')).toHaveCount(0);
        await expect(page.getByLabel('Site')).toHaveValue('Linkedin');
        await expect(page.getByText('python', { exact: true }).first()).toBeVisible();
        await expect(page.getByText('Already-in-DB duplicates by keyword')).toHaveCount(0);

        await page.getByLabel('Site').selectOption('(All)');
        await expect(page.getByText('python', { exact: true }).first()).toBeVisible();
        await expect(page.locator('.keyword-chart .recharts-line')).toHaveCount(2);
    });
});
