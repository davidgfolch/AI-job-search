import { test, expect } from './coverage.fixtures';
import { Page } from '@playwright/test';
import { BASE_URL, setupPageLogging, setupAppBootstrapMocks } from './common.helpers';

const KEYWORD_STATS = {
    items: [
        { date: '2026-11-19', site: 'Indeed', keyword: 'python', reported_total: 40, processed: 20, new: 18, duplicates: 2, duplicate_ids: '91,92' },
        { date: '2026-11-19', site: 'Indeed', keyword: 'java', reported_total: 10, processed: 5, new: 5, duplicates: 0, duplicate_ids: '' },
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

    test('shows the keyword totals chart and the duplicate ids table', async ({ page }) => {
        await page.goto(`${BASE_URL}/statistics`);
        await expect(page.getByText('Keyword totals & duplicates by date')).toBeVisible();
        await expect(page.getByText('Already-in-DB duplicates by keyword')).toBeVisible();
        await expect(page.getByRole('columnheader', { name: 'Duplicate ids' })).toBeVisible();
        await expect(page.getByText('91,92')).toBeVisible();
        await expect(page.getByText('python', { exact: true }).first()).toBeVisible();
    });
});
