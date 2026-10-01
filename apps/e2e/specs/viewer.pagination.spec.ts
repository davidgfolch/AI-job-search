import { test, expect } from './coverage.fixtures';
import { BASE_URL, setupPageLogging, setupSystemMocks, setupPaginatedJobsRoute } from './viewer.helpers';
import { PAGINATED_JOB_COUNT, PAGE_SIZE } from './viewer.mocks';

const jobRows = (page: any) => page.locator('tr[id^="job-row-"]');

test.use({ bypassCSP: true });

test.describe('Viewer pagination with a list that fits on screen', () => {
    /* Tall viewport on purpose: a full page of rows must NOT fill the screen, which is the case that used
       to stall pagination because it could only be triggered by scrolling. */
    test.use({ viewport: { width: 1400, height: 2400 } });

    test.beforeEach(async ({ page }) => {
        setupPageLogging(page);
        await setupSystemMocks(page);
    });

    test('loads every page on its own, without any scrolling', async ({ page }) => {
        const { requestedPages } = await setupPaginatedJobsRoute(page);

        await page.goto(BASE_URL);

        await expect(jobRows(page)).toHaveCount(PAGINATED_JOB_COUNT);
        await expect(page.locator('.list-summary')).toContainText(`${PAGINATED_JOB_COUNT}/${PAGINATED_JOB_COUNT} loaded`);
        expect(requestedPages).toContain(2);
    });

    test('stops requesting pages once every job is loaded', async ({ page }) => {
        const { requestedPages } = await setupPaginatedJobsRoute(page);

        await page.goto(BASE_URL);
        await expect(page.locator('.list-summary')).toContainText(`${PAGINATED_JOB_COUNT}/${PAGINATED_JOB_COUNT} loaded`);
        await page.waitForTimeout(1500);

        // 25 jobs at the default size of 20 is exactly 2 pages: no third request may be issued.
        expect(new Set(requestedPages)).toEqual(new Set([1, 2]));
    });

    test('reaches the end of the list without a scrollbar, which is what broke the old scroll-only trigger', async ({ page }) => {
        await setupPaginatedJobsRoute(page);

        await page.goto(BASE_URL);
        await expect(jobRows(page)).toHaveCount(PAGINATED_JOB_COUNT);

        const measurement = await page.evaluate(() => {
            const container = document.querySelector('.job-table-container') as HTMLElement;
            return { scrollHeight: container.scrollHeight, clientHeight: container.clientHeight, scrollTop: container.scrollTop };
        });

        expect(measurement.scrollHeight).toBeLessThanOrEqual(measurement.clientHeight);
        expect(measurement.scrollTop).toBe(0);
    });
});

test.describe('Viewer pagination with a list taller than the screen', () => {
    test.use({ viewport: { width: 1400, height: 700 } });

    /* Pin the list to a fixed height so it becomes its own scroll container regardless of how the
       surrounding flex chain resolves, and the pages can only be reached by scrolling it. */
    const pinListHeight = async (page: any) => {
        await page.addStyleTag({ content: '.job-table-container { flex: none; height: 400px; }' });
        await page.locator('.job-table-container').waitFor();
    };

    /** Guards the premise of these tests: the end of the list must be past the trigger line, otherwise the
        prefetch margin would load the next page without any scrolling. */
    const expectEndOfListOutOfReach = async (page: any) => {
        const bottom = await page.evaluate(() => (document.querySelector('.job-table-sentinel') as HTMLElement).getBoundingClientRect().bottom);
        expect(bottom, 'end of the list must be below the 200px trigger margin to be out of reach').toBeGreaterThan(700 + 200);
    };

    test.beforeEach(async ({ page }) => {
        setupPageLogging(page);
        await setupSystemMocks(page);
    });

    test('stops at the first page while the end of the list is below the fold', async ({ page }) => {
        const { requestedPages } = await setupPaginatedJobsRoute(page);

        await page.goto(BASE_URL);
        await pinListHeight(page);
        await expect(jobRows(page)).toHaveCount(PAGE_SIZE);
        await expectEndOfListOutOfReach(page);
        await expect(page.locator('.list-summary')).toContainText(`${PAGE_SIZE}/${PAGINATED_JOB_COUNT} loaded`);
        expect(requestedPages).toEqual([1]);
    });

    test('loads the next page when the list is scrolled to the bottom', async ({ page }) => {
        const { requestedPages } = await setupPaginatedJobsRoute(page);

        await page.goto(BASE_URL);
        await pinListHeight(page);
        await expect(jobRows(page)).toHaveCount(PAGE_SIZE);
        await expectEndOfListOutOfReach(page);

        await page.locator('.job-table-container').evaluate((el: HTMLElement) => { el.scrollTop = el.scrollHeight; });

        await expect(jobRows(page)).toHaveCount(PAGINATED_JOB_COUNT);
        await expect(page.locator('.list-summary')).toContainText(`${PAGINATED_JOB_COUNT}/${PAGINATED_JOB_COUNT} loaded`);
        expect(requestedPages).toEqual([1, 2]);
    });
});
