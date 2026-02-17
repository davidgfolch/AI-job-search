import { Page } from '@playwright/test';
import { MOCK_JOB_1, MOCK_JOB_2, MOCK_JOBS_LIST } from './viewer.mocks';
import { BASE_URL, setupPageLogging, setupTimezoneMock } from './common.helpers';

export { BASE_URL, setupPageLogging, setupTimezoneMock };

export async function setupFilterConfigurationMock(page: Page) {
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
}

export function createJobsListRoute(counters: { listRequestCount: number }) {
    return async (route: any) => {
        counters.listRequestCount++;
        await route.fulfill({ json: MOCK_JOBS_LIST });
    };
}

export async function setupJobsMocks(page: Page, counters: { listRequestCount: number }) {
    await page.route(/.*\/api\/jobs(\?|$)/, createJobsListRoute(counters));
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
}

export async function setupWatcherStatsMock(page: Page, counters: { statsRequestCount: number }) {
    await page.route(/.*\/api\/jobs\/watcher-stats.*/, async (route) => {
        counters.statsRequestCount++;
        await route.fulfill({
            json: {
                "101": { total: 10, new_items: 2 }
            }
        });
    });
}

export async function markJobAsApplied(page: Page) {
    await page.getByTitle('Mark as applied').click();
    await page.locator('.modal-content').waitFor({ state: 'visible' });
    await page.getByRole('button', { name: 'OK' }).click();
}

export async function verifyNoRefresh(
    counters: { listRequestCount: number; statsRequestCount: number },
    initialCounts: { list: number; stats: number },
    page: Page
) {
    await page.waitForTimeout(1000);
    if (counters.listRequestCount !== initialCounts.list) {
        throw new Error(`Expected list request count to be ${initialCounts.list}, but got ${counters.listRequestCount}`);
    }
    if (counters.statsRequestCount !== initialCounts.stats) {
        throw new Error(`Expected stats request count to be ${initialCounts.stats}, but got ${counters.statsRequestCount}`);
        throw new Error(`Expected stats request count to be ${initialCounts.stats}, but got ${counters.statsRequestCount}`);
    }
}
