import { test, expect } from '@playwright/test';
import { 
    BASE_URL,
    setupPageLogging,
    setupFilterConfigurationMock,
    setupTimezoneMock,
    setupJobsMocks,
    setupWatcherStatsMock,
    markJobAsApplied,
    verifyNoRefresh
} from './watcher_refresh.helpers';

test.describe('Watcher Stability', () => {
    test('should NOT refresh list with new watcher items when changing job state', async ({ page }) => {
        const counters = { statsRequestCount: 0, listRequestCount: 0 };
        setupPageLogging(page);
        await setupFilterConfigurationMock(page);
        await setupTimezoneMock(page);
        await setupJobsMocks(page, counters);
        await setupWatcherStatsMock(page, counters);
        await page.goto(BASE_URL);
        // Verify initial list
        await expect(page.locator('#job-row-1')).toBeVisible();
        await expect(page.locator('#job-row-2')).toBeVisible();
        await expect(page.locator('.watcher-badge-inline', { hasText: '+2' })).toBeVisible();
        expect(counters.statsRequestCount).toBeGreaterThan(0);
        const initialCounts = { 
            list: counters.listRequestCount, 
            stats: counters.statsRequestCount 
        };
        await page.locator('#job-row-1').click();
        await expect(page.locator('#job-detail-title')).toContainText('Frontend Engineer');
        await markJobAsApplied(page);
        await expect(page.locator('#job-row-1')).not.toBeVisible();
        await expect(page.locator('#job-row-2')).toBeVisible();
        await verifyNoRefresh(counters, initialCounts, page);
        expect(counters.listRequestCount, 'Should NOT have refetched the jobs list').toBe(initialCounts.list);
        expect(counters.statsRequestCount, 'Should NOT have re-polled watcher stats').toBe(initialCounts.stats);
        await expect(page.locator('tr[id^="job-row-"]')).toHaveCount(1);
    });
});
