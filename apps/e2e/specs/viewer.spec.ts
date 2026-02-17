import { test, expect } from '@playwright/test';
import { MOCK_JOB_1, MOCK_JOB_2, MOCK_JOBS_LIST, MOCK_SEARCH_BACKEND } from './viewer.mocks';

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

        // Wait for the page to be fully loaded
        await page.waitForLoadState('domcontentloaded');
        
        // Wait for filter configurations to load (this determines initial expanded state)
        await page.waitForResponse(resp => resp.url().includes('api/filter-configurations') && resp.status() === 200);
        
        // Check if filters are already expanded
        const filterContent = page.locator('.filters-content');
        const isExpanded = await filterContent.count() > 0;
        
        // Only click toggle if filters are not expanded
        if (!isExpanded) {
            await page.locator('#toggle-filters').click({ force: true });
        }
        
        // Wait for search input to be visible
        await page.locator('#filter-search').waitFor({ state: 'visible', timeout: 10000 });

        // Fill search and wait for the response
        const responsePromise = page.waitForResponse(resp => 
            resp.url().includes('search=Backend') && resp.status() === 200
        );
        await page.locator('#filter-search').fill('Backend');
        await responsePromise;

        // Wait for the list to update
        // We expect Frontend Engineer to disappear and Backend Developer to remain
        await expect(page.locator('#job-row-1')).not.toBeVisible();
        await expect(page.locator('#job-row-2')).toBeVisible();
    });
    test('should remove job from list view and select next on state change', async ({ page }) => {
        // Unroute the default handler from beforeEach to avoid conflicts
        await page.unroute(/.*\/api\/jobs.*/);

        // Override mock for this test to handle state change flow
        let listRequestCount = 0;
        await page.route(/.*\/api\/jobs.*/, async (route) => {
            const url = route.request().url();
            
            // Handle applied-by-company request (keep default behavior)
            if (url.includes('/applied-by-company')) {
                 await route.fulfill({ json: [] });
                 return;
            }

            // Handle single job request (e.g. /api/jobs/1)
            // Note: This regex needs to be precise to not match list with query params
            if (/\/api\/jobs\/\d+$/.test(url)) {
                 const jobId = url.split('/').pop();
                 if (jobId === '1') await route.fulfill({ json: MOCK_JOB_1 });
                 if (jobId === '2') await route.fulfill({ json: MOCK_JOB_2 });
                 return;
            }

            // List requests (default fallthrough if not single job)
            if (/\/api\/jobs(\?|$)/.test(url)) {
                listRequestCount++;
                if (listRequestCount === 1) {
                    // Initial load: return both jobs
                    await route.fulfill({ json: MOCK_JOBS_LIST });
                } else {
                    // Second load (after update): return only job 2
                    // We return job 2 as the single item
                    await route.fulfill({ 
                        json: { 
                            ...MOCK_JOBS_LIST, 
                            items: [MOCK_JOB_2], 
                            total: 1 
                        } 
                    });
                }
                return;
            }

            // Fallback
            await route.continue();
        });

        // Mock the update request
        await page.route(/.*\/api\/jobs\/1/, async (route) => {
            if (route.request().method() === 'PATCH') {
                await route.fulfill({ json: { ...MOCK_JOB_1, applied: true } });
            } else {
                await route.continue();
            }
        });

        await page.goto('http://127.0.0.1:5173');
        
        // 1. Select the first job
        await page.locator('#job-row-1').click();
        await expect(page.locator('#job-detail-title')).toContainText('Frontend Engineer');

        // 2. Click "Mark as applied" button
        await page.getByTitle('Mark as applied').click();
        
        // Wait for modal to be visible and confirm
        await expect(page.locator('.modal-content')).toBeVisible();
        await page.getByRole('button', { name: 'OK' }).click();
        
        // Wait for the update to complete
        await page.waitForTimeout(1000);

        // 3. Verify job 1 is removed from list
        // (The job should be removed locally via optimistic update)
        await expect(page.locator('#job-row-1')).not.toBeVisible();
        await expect(page.locator('#job-row-2')).toBeVisible();
    });
});
