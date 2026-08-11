import { test, expect } from './coverage.fixtures';
import {
    BASE_URL,
    setupPageLogging,
    setupSystemMocks,
    setupDefaultJobsRoute,
} from './viewer.helpers';
import { MOCK_JOB_2, MOCK_JOB_NO_SALARY, MOCK_JOBS_LIST, SALARY_HISTORY_ENTRIES } from './viewer.mocks';

test.use({
    bypassCSP: true,
});

test.describe('Salary History E2E', () => {
    test.beforeEach(async ({ page }) => {
        setupPageLogging(page);
        await setupSystemMocks(page);
        await setupDefaultJobsRoute(page);
    });

    test('should show company salary history indicator for job without salary', async ({ page }) => {
        await page.route(/.*\/api\/jobs\/history\/by-company.*/, async (route) => {
            await route.fulfill({ contentType: 'application/json', json: SALARY_HISTORY_ENTRIES });
        });
        await page.route(/.*\/api\/jobs(\?|$)/, async (route) => {
            await route.fulfill({ json: { ...MOCK_JOBS_LIST, items: [MOCK_JOB_NO_SALARY, MOCK_JOB_2] } });
        });
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await expect(page.locator('.job-info')).toContainText('Company salary history');
        await expect(page.locator('.job-info')).toContainText('120k');
        await page.getByTitle('View full history').click();
        await expect(page.locator('.modal-content')).toContainText('Salary History');
        await expect(page.locator('.modal-content')).toContainText('Senior Frontend Engineer');
    });

    test('should open salary history modal for job with salary', async ({ page }) => {
        await page.route(/.*\/api\/jobs\/1\/history.*/, async (route) => {
            await route.fulfill({ contentType: 'application/json', json: SALARY_HISTORY_ENTRIES });
        });
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await page.getByTitle('View salary history').click();
        await expect(page.locator('.modal-content')).toContainText('Salary History');
        await expect(page.locator('.modal-content')).toContainText('Frontend Engineer');
        await expect(page.locator('.modal-content')).toContainText('120k');
    });

    test('should show empty state when no salary history exists', async ({ page }) => {
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await page.getByTitle('View salary history').click();
        await expect(page.locator('.modal-content')).toContainText('No salary history recorded yet');
    });
});
