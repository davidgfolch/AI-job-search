import { test, expect } from '@playwright/test';
import { MOCK_JOB_1, MOCK_JOB_2, MOCK_JOBS_LIST } from './viewer.mocks';

test.describe('Watcher Stability', () => {
    test('should NOT refresh list with new watcher items when changing job state', async ({ page }) => {
        let statsRequestCount = 0;
        let listRequestCount = 0;

        // Mock filter configurations
        await page.route(/.*\/api\/filter-configurations.*/, async (route) => {
            await route.fulfill({
                contentType: 'application/json',
                json: [
                    {
                        id: 101,
                        name: "Backend Filter",
                        filters: { search: "Backend" },
                        pinned: true,
                        statistics: true
                    }
                ]
            });
        });

        // Mock system timezone
        await page.route(/.*\/api\/system\/timezone.*/, async (route) => {
            await route.fulfill({ json: { offset_minutes: 0 } });
        });

        // Default handler for jobs list
        await page.route(/.*\/api\/jobs(\?|$)/, async (route) => {
            listRequestCount++;
            await route.fulfill({ json: MOCK_JOBS_LIST });
        });

        // Mock single job request
        await page.route(/.*\/api\/jobs\/1$/, async (route) => {
            if (route.request().method() === 'PATCH') {
                await route.fulfill({ json: { ...MOCK_JOB_1, applied: true } });
            } else {
                await route.fulfill({ json: MOCK_JOB_1 });
            }
        });
        
        await page.route(/.*\/api\/jobs\/2$/, async (route) => {
            await route.fulfill({ json: MOCK_JOB_2 });
        });

        // Mock watcher stats
        await page.route(/.*\/api\/jobs\/watcher-stats.*/, async (route) => {
            statsRequestCount++;
            // Return 2 new items for the filter
            await route.fulfill({
                json: {
                    "101": { total: 10, new_items: 2 }
                }
            });
        });

        await page.goto('http://127.0.0.1:5173');

        // Verify initial list
        await expect(page.locator('#job-row-1')).toBeVisible();
        await expect(page.locator('#job-row-2')).toBeVisible();

        // Wait for watcher badge to appear
        const badge = page.locator('.watcher-badge-inline', { hasText: '+2' });
        await expect(badge).toBeVisible();
        expect(statsRequestCount).toBeGreaterThan(0);
        
        // Save initial list call count
        const initialListCalls = listRequestCount;
        const initialStatsCalls = statsRequestCount;

        // 1. Select the first job
        await page.locator('#job-row-1').click();
        
        // 2. Click "Mark as applied"
        // This will remove it from the list because of the default filters (applied: false)
        await page.getByTitle('Mark as applied').click();

        // 3. Verify job 1 is removed from list LOCALLY
        await expect(page.locator('#job-row-1')).not.toBeVisible();
        await expect(page.locator('#job-row-2')).toBeVisible();

        // 4. Verify selection moved to job 2
        await expect(page.locator('#job-detail-title')).toContainText('Backend Developer');

        // 5. CRITICAL: Verify NO new list requests or stats requests were triggered
        // A short wait might be needed to ensure no async triggers happen
        await page.waitForTimeout(1000);
        
        expect(listRequestCount, 'Should NOT have refetched the jobs list').toBe(initialListCalls);
        expect(statsRequestCount, 'Should NOT have re-polled watcher stats').toBe(initialStatsCalls);

        // 6. Verify table still only shows Job 2, and DOES NOT show the "new jobs" (+2) found by the watcher
        // The watcher found 2 new jobs, but they should only load if we click the configuration.
        // If they had loaded, the total count would have changed or new rows appeared.
        await expect(page.locator('tr[id^="job-row-"]')).toHaveCount(1);
    });
});
