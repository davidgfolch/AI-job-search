import { test, expect } from './coverage.fixtures';
import {
    BASE_URL,
    setupPageLogging,
    setupSystemMocks,
    setupDefaultJobsRoute,
} from './viewer.helpers';
import { MOCK_JOB_2, MOCK_JOB_WITH_CALC_COMMENTS, MOCK_JOBS_LIST } from './viewer.mocks';

test.use({
    bypassCSP: true,
});

const SALARY_CALC_RESPONSE = {
    gross_year: '42000',
    parsed_equation: '40 * 8 * 220',
    year_tax: '6000',
    year_tax_equation: '42000 * 0.14',
    net_year: '36000',
    net_month: '3000',
    freelance_tax: '0',
};

const SALARY_CALC_POST = (req: { method(): string; url(): string }) => req.method() === 'POST' && /\/api\/salary\/calculate/.test(req.url());
const JOB_1_PATCH = (req: { method(): string; url(): string }) => req.method() === 'PATCH' && /\/api\/jobs\/1$/.test(req.url());

test.describe('Salary Calculator E2E', () => {
    test.beforeEach(async ({ page }) => {
        setupPageLogging(page);
        await setupSystemMocks(page);
        await setupDefaultJobsRoute(page);
        await page.route(/.*\/api\/salary\/calculate.*/, async (route) => {
            await route.fulfill({ contentType: 'application/json', json: SALARY_CALC_RESPONSE });
        });
    });

    const openCalculator = async (page: any) => {
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await expect(page.locator('#job-detail-title')).toContainText('Frontend Engineer');
        await page.getByRole('button', { name: '🧮 Freelance' }).click();
        await expect(page.locator('.salary-calculator')).toBeVisible();
    };

    test('should calculate salary and show results', async ({ page }) => {
        await openCalculator(page);
        await expect(page.locator('.salary-calculator-results')).toBeVisible();
        await expect(page.locator('.salary-calculator-results')).toContainText('42000');
        await expect(page.locator('.salary-calculator-results')).toContainText('36000');
    });

    test('should switch between calc modes', async ({ page }) => {
        await openCalculator(page);
        await page.locator('#calc-mode').selectOption('hoursPerWeek');
        await expect(page.locator('#calc-hours-week')).toBeVisible();
        await expect(page.locator('#calc-hours-week')).toHaveValue('40');
        await page.locator('#calc-mode').selectOption('daysPerMonth');
        await expect(page.locator('#calc-days-month')).toBeVisible();
        await expect(page.locator('#calc-days-month')).toHaveValue('20');
    });

    test('should save calculation to job comments', async ({ page }) => {
        await openCalculator(page);
        await expect(page.locator('.salary-calculator-results')).toBeVisible();
        const patchRequest = page.waitForRequest(JOB_1_PATCH);
        await page.getByRole('button', { name: '💾 Save' }).click();
        const request = await patchRequest;
        expect(request.postDataJSON().comments).toContain('SALARY_CALC_DATA');
    });

    test('should auto-open calculator when comments contain saved params', async ({ page }) => {
        await page.route(/.*\/api\/jobs(\?|$)/, async (route) => {
            await route.fulfill({ json: { ...MOCK_JOBS_LIST, items: [MOCK_JOB_WITH_CALC_COMMENTS, MOCK_JOB_2] } });
        });
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await expect(page.locator('.salary-calculator')).toBeVisible();
        await expect(page.locator('#calc-rate-classic')).toHaveValue('40');
    });

    test('should delete salary information', async ({ page }) => {
        await openCalculator(page);
        const patchRequest = page.waitForRequest(JOB_1_PATCH);
        await page.getByTitle('Delete salary information').click();
        expect((await patchRequest).postDataJSON()).toEqual({ salary: null });
    });

    test('should open gross year calculator in a new tab', async ({ page }) => {
        await page.context().route('https://tecalculo.com/**', async (route) => {
            await route.fulfill({ status: 200, contentType: 'text/html', body: '<html><body></body></html>' });
        });
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        const popupPromise = page.waitForEvent('popup');
        await page.getByRole('button', { name: '🧮 Gross year' }).click();
        const popup = await popupPromise;
        await popup.waitForURL('https://tecalculo.com/calculadora-de-sueldo-neto');
        await popup.close();
    });
});
