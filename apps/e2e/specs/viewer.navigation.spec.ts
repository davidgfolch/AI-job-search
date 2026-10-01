import type { Page } from '@playwright/test';
import { test, expect } from './coverage.fixtures';
import { BASE_URL, setupPageLogging, setupSystemMocks, setupPaginatedJobsRoute } from './viewer.helpers';
import { PAGE_SIZE, PAGINATED_JOB_COUNT } from './viewer.mocks';

test.use({ bypassCSP: true, viewport: { width: 1400, height: 700 } });

/* A frame far shorter than the loaded page, so stepping through it has to leave the visible frame. It is
   pinned so the list is its own scroll container regardless of how the surrounding flex chain resolves. */
const FRAME_HEIGHT = 300;

const pinListHeight = async (page: Page) => {
    await page.addStyleTag({ content: `.job-table-container { flex: none; height: ${FRAME_HEIGHT}px; }` });
    await page.locator('.job-table-container').waitFor();
};

const expectSelectedRow = async (page: Page, jobId: number) =>
    expect(page.locator('.job-table tbody tr.selected')).toHaveAttribute('id', `job-row-${jobId}`);

/** The sticky header floats over the top of the scroll port, so that part of the frame is not readable and a
    row parked there does not read as visible. Both gaps must be inside the frame for the job to be seen. */
const expectSelectedRowReadable = async (page: Page, step: string) => {
    const { aboveHeader, belowEdge } = await page.evaluate(() => {
        const list = document.querySelector('.job-table-container') as HTMLElement;
        const head = document.querySelector('.job-table thead') as HTMLElement;
        const row = document.querySelector('.job-table tbody tr.selected') as HTMLElement;
        const frameTop = list.getBoundingClientRect().top + head.getBoundingClientRect().height;
        return {
            aboveHeader: row.getBoundingClientRect().top - frameTop,
            belowEdge: row.getBoundingClientRect().bottom - list.getBoundingClientRect().bottom,
        };
    });
    expect(aboveHeader, `${step}: the sticky header must not cover the selected row`).toBeGreaterThanOrEqual(-1);
    expect(belowEdge, `${step}: the selected row must not fall below the list`).toBeLessThanOrEqual(1);
};

test.beforeEach(async ({ page }) => {
    setupPageLogging(page);
    await setupSystemMocks(page);
    await setupPaginatedJobsRoute(page);
});

test.describe('Next and previous job keep the selection inside the visible frame', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto(BASE_URL);
        await pinListHeight(page);
        await page.locator('#job-row-1').waitFor();
    });

    test('walks down with Alt+n without ever losing the selected row', async ({ page }) => {
        await page.locator('#job-row-1').click();

        for (let jobId = 2; jobId <= PAGE_SIZE; jobId++) {
            await page.keyboard.press('Alt+n');
            await expectSelectedRow(page, jobId);
            await expectSelectedRowReadable(page, `job ${jobId}`);
        }
    });

    test('walks back up with Alt+p without ever losing the selected row', async ({ page }) => {
        await page.locator('#job-row-1').click();

        for (let jobId = 2; jobId <= PAGE_SIZE; jobId++) await page.keyboard.press('Alt+n');
        await expectSelectedRow(page, PAGE_SIZE);

        for (let jobId = PAGE_SIZE - 1; jobId >= 1; jobId--) {
            await page.keyboard.press('Alt+p');
            await expectSelectedRow(page, jobId);
            await expectSelectedRowReadable(page, `job ${jobId}`);
        }
    });

    test('walks down and back up with the next and previous buttons', async ({ page }) => {
        await page.locator('#job-row-1').click();
        const next = page.locator('.list-header-actions .nav-button').last();
        const previous = page.locator('.list-header-actions .nav-button').first();

        for (let jobId = 2; jobId <= PAGE_SIZE; jobId++) {
            await next.click();
            await expectSelectedRow(page, jobId);
            await expectSelectedRowReadable(page, `job ${jobId}`);
        }
        for (let jobId = PAGE_SIZE - 1; jobId >= 1; jobId--) {
            await previous.click();
            await expectSelectedRow(page, jobId);
            await expectSelectedRowReadable(page, `job ${jobId}`);
        }
    });

    test('brings into view the job that a page loaded past the end of the list starts at', async ({ page }) => {
        await page.locator('#job-row-1').click();

        for (let jobId = 2; jobId <= PAGE_SIZE; jobId++) await page.keyboard.press('Alt+n');
        await expectSelectedRow(page, PAGE_SIZE);

        await page.keyboard.press('Alt+n');

        // One step past the last loaded job loads the next page and selects its first job, which is appended
        // below the frame and would stay out of sight without scrolling down to it.
        await expectSelectedRow(page, PAGE_SIZE + 1);
        await expectSelectedRowReadable(page, `job ${PAGE_SIZE + 1}`);
        await expect(page.locator('.list-summary')).toContainText(`/${PAGINATED_JOB_COUNT} loaded`);
    });
});
