import { test, expect } from './coverage.fixtures';
import {
    BASE_URL,
    setupPageLogging,
    setupSystemMocks,
    setupDefaultJobsRoute,
} from './viewer.helpers';

test.use({
    bypassCSP: true,
});

const PATCH_JOB = (req: { method(): string; url(): string }) => req.method() === 'PATCH' && /\/api\/jobs\/\d+$/.test(req.url());

test.describe('Viewer Keyboard Shortcuts E2E', () => {
    test.beforeEach(async ({ page }) => {
        setupPageLogging(page);
        await setupSystemMocks(page);
        await setupDefaultJobsRoute(page);
    });

    test('should ignore the selected job with Alt+i', async ({ page }) => {
        const patchRequest = page.waitForRequest(PATCH_JOB);
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await page.keyboard.press('Alt+i');
        expect((await patchRequest).postDataJSON()).toEqual({ ignored: true });
    });

    test('should open the apply modal with Alt+a', async ({ page }) => {
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await page.keyboard.press('Alt+a');
        await expect(page.locator('.modal-content')).toBeVisible();
        await expect(page.getByText('Mark as Applied')).toBeVisible();
    });

    test('should select the next job with Alt+n', async ({ page }) => {
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await expect(page.locator('#job-detail-title')).toContainText('Frontend Engineer');
        await page.keyboard.press('Alt+n');
        await expect(page.locator('#job-detail-title')).toContainText('Backend Developer');
    });

    test('should select the previous job with Alt+p', async ({ page }) => {
        await page.goto(BASE_URL);
        await page.locator('#job-row-2').click();
        await expect(page.locator('#job-detail-title')).toContainText('Backend Developer');
        await page.keyboard.press('Alt+p');
        await expect(page.locator('#job-detail-title')).toContainText('Frontend Engineer');
    });

    test('should open the selected job url with Alt+o', async ({ page }) => {
        await page.context().route('http://example.com/**', async (route) => {
            await route.fulfill({ status: 200, contentType: 'text/html', body: '<html><body></body></html>' });
        });
        const popupPromise = page.waitForEvent('popup');
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await page.keyboard.press('Alt+o');
        const popup = await popupPromise;
        await popup.waitForURL('http://example.com/1');
        expect(popup.url()).toBe('http://example.com/1');
        await popup.close();
    });

    test('should focus the jobs list with Alt+l', async ({ page }) => {
        await page.goto(BASE_URL);
        await expect(page.locator('#job-row-1')).toBeVisible();
        await page.keyboard.press('Alt+l');
        const activeClass = await page.evaluate(() => document.activeElement?.className || '');
        expect(activeClass).toContain('job-table-container');
    });

    test('should focus the job detail with Alt+j', async ({ page }) => {
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await page.keyboard.press('Alt+j');
        const activeClass = await page.evaluate(() => document.activeElement?.className || '');
        expect(activeClass).toContain('job-detail-content');
    });

    test('should disable shortcuts when toggled off', async ({ page }) => {
        let patched = false;
        page.on('request', req => {
            if (PATCH_JOB(req)) patched = true;
        });
        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await page.getByTitle('Keyboard shortcuts enabled').click();
        await page.keyboard.press('Alt+i');
        await page.waitForTimeout(500);
        expect(patched).toBe(false);
    });
});
