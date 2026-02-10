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

        // Mock system timezone
        await page.route(/.*\/api\/system\/timezone.*/, async (route) => {
            await route.fulfill({
                contentType: 'application/json',
                json: { offset_minutes: 0 }
            });
        });

        // Mock filter configurations
        await page.route(/.*\/api\/filter-configurations.*/, async (route) => {
            await route.fulfill({
                contentType: 'application/json',
                json: []
            });
        });

        // Default handler for jobs list
        await page.route(/.*\/api\/jobs.*/, async (route) => {
            const url = route.request().url();
            console.log('MOCKING REQUEST:', url);

            // Handle applied-by-company request
            if (url.includes('/applied-by-company')) {
                 await route.fulfill({ json: [] });
                return;
            }

            // Handle single job request (e.g. /api/jobs/1)
            if (/\/api\/jobs\/\d+$/.test(url)) {
                await route.fulfill({ json: MOCK_JOB_1 });
                return;
            }

            // Handle search query - check if search parameter is present
            // Handle both search=Backend and search=Frontend (for completeness)
            const searchParam = new URL(url).searchParams.get('search');
            if (searchParam === 'Backend') {
                console.log('REPLYING WITH BACKEND SEARCH RESULTS');
                await route.fulfill({ json: MOCK_SEARCH_BACKEND });
                return;
            }

            // Default list response
            if (/\/api\/jobs(\?|$)/.test(url)) {
                console.log('REPLYING WITH DEFAULT JOB LIST');
                await route.fulfill({ json: MOCK_JOBS_LIST });
                return;
            }
            
            console.log('UNHANDLED REQUEST:', url);
            route.continue();
        });
    });

    test('should load and display jobs', async ({ page }) => {
        await page.goto('http://127.0.0.1:5173');
        await expect(page.locator('table')).toBeVisible();
        await expect(page.locator('#job-row-1')).toBeVisible();
        await expect(page.locator('#job-row-1')).toContainText('Frontend Engineer');
        await expect(page.locator('#job-row-2')).toBeVisible();
        await expect(page.locator('#job-row-2')).toContainText('Backend Developer');
    });

    test('should view job details when clicking a row', async ({ page }) => {
        await page.goto('http://127.0.0.1:5173');
        await page.locator('#job-row-1').click();

        // Wait for detail view
        await expect(page.locator('#job-detail-title')).toBeVisible();
        await expect(page.locator('#job-detail-title')).toContainText('Frontend Engineer');
        await expect(page.getByText('Job Description')).toBeVisible();
    });

    test('should filter jobs', async ({ page }) => {
        await page.goto('http://127.0.0.1:5173');

        // Ensure filters are expanded
        const searchInput = page.locator('#filter-search');
        if (!await searchInput.isVisible()) {
            await page.locator('#toggle-filters').click();
        }

        // Fill search and wait for the response
        const responsePromise = page.waitForResponse(resp => 
            resp.url().includes('search=Backend') && resp.status() === 200
        );
        await searchInput.fill('Backend');
        await responsePromise;

        // Wait for the list to update
        // We expect Frontend Engineer to disappear and Backend Developer to remain
        await expect(page.locator('#job-row-1')).not.toBeVisible();
        await expect(page.locator('#job-row-2')).toBeVisible();
    });
});
