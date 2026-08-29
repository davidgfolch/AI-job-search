import { test, expect } from './coverage.fixtures';
import { 
    BASE_URL, 
    setupPageLogging, 
    setupSystemMocks, 
    setupDefaultJobsRoute,
    setupStateChangeJobsRoute,
    setupJobUpdateRoute,
    setupBulkJobsRoute,
    toggleFiltersIfNeeded,
    waitForFilterConfigurations,
    searchJobs
} from './viewer.helpers';

test.use({
    bypassCSP: true,
});

test.describe('Viewer E2E', () => {
    test.beforeEach(async ({ page }) => {
        setupPageLogging(page);
        await setupSystemMocks(page);
        await setupDefaultJobsRoute(page);
    });

    test('should load and display jobs', async ({ page }) => {
        await page.goto(BASE_URL);
        await expect(page.locator('table')).toBeVisible();
        await expect(page.locator('#job-row-1')).toBeVisible();
        await expect(page.locator('#job-row-1')).toContainText('Frontend Engineer');
        await expect(page.locator('#job-row-2')).toBeVisible();
        await expect(page.locator('#job-row-2')).toContainText('Backend Developer');
    });

    test('should view job details when clicking a row', async ({ page }) => {
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await expect(page.locator('#job-detail-title')).toBeVisible();
        await expect(page.locator('#job-detail-title')).toContainText('Frontend Engineer');
        await expect(page.getByText('Job Description')).toBeVisible();
    });

    test('should filter jobs', async ({ page }) => {
        await page.goto(BASE_URL);
        await page.waitForLoadState('domcontentloaded');
        await waitForFilterConfigurations(page);
        await toggleFiltersIfNeeded(page);
        await searchJobs(page, 'Backend');
        await expect(page.locator('#job-row-1')).not.toBeVisible();
        await expect(page.locator('#job-row-2')).toBeVisible();
    });

    test('should remove job from list view and select next on state change', async ({ page }) => {
        await page.unroute(/.*\/api\/jobs.*/);
        await setupStateChangeJobsRoute(page);
        await setupJobUpdateRoute(page);
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await expect(page.locator('#job-detail-title')).toContainText('Frontend Engineer');
        await page.locator('.list-header-actions').getByTitle('Mark as applied').click();
        await expect(page.locator('.modal-content')).toBeVisible();
        await page.getByRole('button', { name: 'OK' }).click();
        await page.waitForTimeout(1000);
        await expect(page.locator('#job-row-1')).not.toBeVisible();
        await expect(page.locator('#job-row-2')).toBeVisible();
    });

    test('should apply job when pressing Enter in the applied modal', async ({ page }) => {
        await page.unroute(/.*\/api\/jobs.*/);
        await setupStateChangeJobsRoute(page);
        await setupJobUpdateRoute(page);
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await page.locator('.list-header-actions').getByTitle('Mark as applied').click();
        await expect(page.locator('.modal-content')).toBeVisible();
        await page.keyboard.press('Enter');
        await page.waitForTimeout(1000);
        await expect(page.locator('#job-row-1')).not.toBeVisible();
        await expect(page.locator('#job-row-2')).toBeVisible();
    });

    test('should bulk ignore selected jobs', async ({ page }) => {
        await setupBulkJobsRoute(page);
        await page.goto(BASE_URL);
        await page.locator('#job-table-select-1').check();
        await page.locator('#job-table-select-2').check();
        const bulkRequest = page.waitForRequest(req => req.method() === 'POST' && /\/api\/jobs\/bulk$/.test(req.url()));
        await page.locator('.list-header-actions').getByTitle('Mark as ignored').click();
        await page.getByRole('button', { name: 'Confirm' }).click();
        const request = await bulkRequest;
        expect(request.postDataJSON()).toEqual({ ids: [1, 2], update: { ignored: true } });
        await expect(page.locator('#job-row-1')).not.toBeVisible();
        await expect(page.locator('#job-row-2')).not.toBeVisible();
    });

    test('should confirm bulk ignore when pressing Enter', async ({ page }) => {
        await setupBulkJobsRoute(page);
        await page.goto(BASE_URL);
        await page.locator('#job-table-select-1').check();
        await page.locator('#job-table-select-2').check();
        const bulkRequest = page.waitForRequest(req => req.method() === 'POST' && /\/api\/jobs\/bulk$/.test(req.url()));
        await page.locator('.list-header-actions').getByTitle('Mark as ignored').click();
        await expect(page.locator('.modal-content')).toBeVisible();
        await page.keyboard.press('Enter');
        const request = await bulkRequest;
        expect(request.postDataJSON()).toEqual({ ids: [1, 2], update: { ignored: true } });
        await expect(page.locator('.modal-content')).not.toBeVisible();
    });

    test('should cancel bulk ignore when pressing Escape', async ({ page }) => {
        await setupBulkJobsRoute(page);
        await page.goto(BASE_URL);
        await page.locator('#job-table-select-1').check();
        await page.locator('#job-table-select-2').check();
        await page.locator('.list-header-actions').getByTitle('Mark as ignored').click();
        await expect(page.locator('.modal-content')).toBeVisible();
        await page.keyboard.press('Escape');
        await expect(page.locator('.modal-content')).not.toBeVisible();
        await expect(page.locator('#job-row-1')).toBeVisible();
        await expect(page.locator('#job-row-2')).toBeVisible();
    });

    test('should bulk delete all selected jobs', async ({ page }) => {
        await setupBulkJobsRoute(page);
        await page.goto(BASE_URL);
        await page.locator('#job-table-select-all').check();
        const bulkRequest = page.waitForRequest(req => req.method() === 'POST' && /\/api\/jobs\/bulk\/delete/.test(req.url()));
        await page.locator('.tab-button.delete-button').click();
        await page.getByRole('button', { name: 'Confirm' }).click();
        const request = await bulkRequest;
        expect(request.postDataJSON().select_all).toBe(true);
        await expect(page.locator('tr[id^="job-row-"]')).toHaveCount(0);
    });
});
