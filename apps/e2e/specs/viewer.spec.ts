import { test, expect } from '@playwright/test';
import { 
    BASE_URL, 
    setupPageLogging, 
    setupSystemMocks, 
    setupDefaultJobsRoute,
    setupStateChangeJobsRoute,
    setupJobUpdateRoute,
    toggleFiltersIfNeeded,
    waitForFilterConfigurations,
    searchJobs
} from './viewer.helpers';

test.use({
    bypassCSP: true,
    launchOptions: {
        args: ['--disable-web-security'],
    },
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
        await page.getByTitle('Mark as applied').click();
        await expect(page.locator('.modal-content')).toBeVisible();
        await page.getByRole('button', { name: 'OK' }).click();
        await page.waitForTimeout(1000);
        await expect(page.locator('#job-row-1')).not.toBeVisible();
        await expect(page.locator('#job-row-2')).toBeVisible();
    });
});
