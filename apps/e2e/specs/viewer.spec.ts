import { test, expect } from '@playwright/test';
import { MOCK_JOB_1, MOCK_JOBS_LIST, MOCK_SEARCH_BACKEND } from './viewer.mocks';

test.use({
    bypassCSP: true,
    launchOptions: {
        args: ['--disable-web-security'],
    },
});

test.describe('Viewer E2E', () => {
    test.beforeEach(async ({ page }) => {
        // Log console messages from the browser
        page.on('console', msg => console.log('PAGE LOG:', msg.text()));
        page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
        page.on('requestfailed', request => console.log('REQUEST FAILED:', request.url(), request.failure()?.errorText));

        // Default handler for jobs list
        // Using a regex to match any API call to /jobs
        await page.route(/.*\/api\/jobs.*/, async (route) => {
            const url = route.request().url();
            console.log('MOCKING REQUEST:', url);

            // Handle applied-by-company request
            if (url.includes('/applied-by-company')) {
                 await route.fulfill({
                    contentType: 'application/json',
                    json: []
                });
                return;
            }

            // Handle single job request (e.g. /api/jobs/1)
            // Use strict regex to avoid matching list requests that might happen to look similar
            if (/\/api\/jobs\/\d+$/.test(url)) {
                console.log('MOCKING SINGLE JOB:', url);
                await route.fulfill({
                    contentType: 'application/json',
                    json: MOCK_JOB_1
                });
                return;
            }

            // Handle search query
            if (url.includes('search=Backend')) {
                await route.fulfill({
                    contentType: 'application/json',
                    json: MOCK_SEARCH_BACKEND
                });
                return;
            }

            // Default list response for /api/jobs (without ID)
             if (/\/api\/jobs(\?|$)/.test(url)) {
                 console.log('MOCKING JOB LIST:', url);
                await route.fulfill({
                    contentType: 'application/json',
                    json: MOCK_JOBS_LIST
                });
                return;
            }
            
            console.log('UNHANDLED REQUEST:', url);
            route.continue();
        });
    });

    test('should load and display jobs', async ({ page }) => {
        await page.goto('http://127.0.0.1:5173');
        await expect(page.locator('table')).toBeVisible();
        await expect(page.getByText('Frontend Engineer', { exact: true })).toBeVisible();
        await expect(page.getByText('Backend Developer', { exact: true })).toBeVisible();
    });

    test('should view job details when clicking a row', async ({ page }) => {
        await page.goto('http://127.0.0.1:5173');
        await page.getByText('Frontend Engineer', { exact: true }).click();

        // Wait for detail view
        await expect(page.getByRole('heading', { name: 'Frontend Engineer' })).toBeVisible();
        await expect(page.getByText('Job Description')).toBeVisible();
    });

    test('should filter jobs', async ({ page }) => {
        await page.goto('http://127.0.0.1:5173');

        // Fill search
        await page.getByPlaceholder('Search jobs...').fill('Backend');

        // Wait for the list to update
        // We expect Frontend Engineer to disappear and Backend Developer to remain
        await expect(page.getByText('Frontend Engineer', { exact: true })).not.toBeVisible();
        await expect(page.getByText('Backend Developer', { exact: true })).toBeVisible();
    });
});
