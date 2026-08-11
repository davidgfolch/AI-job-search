import { test, expect } from './coverage.fixtures';
import { BASE_URL, setupPageLogging } from './viewer.helpers';
import { setupSettingsMocks } from './settings.helpers';

test.use({
    bypassCSP: true,
});

const ENV_BULK_POST = (req: { method(): string; url(): string }) => req.method() === 'POST' && /\/api\/settings\/env-bulk/.test(req.url());
const SCRAPPER_STATE_POST = (req: { method(): string; url(): string }) => req.method() === 'POST' && /\/api\/settings\/scrapper-state/.test(req.url());

test.describe('Settings E2E', () => {
    test.beforeEach(async ({ page }) => {
        setupPageLogging(page);
        await setupSettingsMocks(page);
    });

    test('should render env groups and scrapper state', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings`);
        await expect(page.locator('#env-SCRAPPER_JOBS_SEARCH')).toBeVisible();
        await expect(page.locator('#env-SCRAPPER_JOBS_SEARCH')).toHaveValue('react, python');
        await expect(page.locator('.env-group').filter({ hasText: 'Scrapper' })).toBeVisible();
        await expect(page.locator('.scrapper-editor')).toContainText('linkedin');
    });

    test('should update env settings', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings`);
        await page.locator('#env-SCRAPPER_JOBS_SEARCH').fill('react, python, go');
        const postRequest = page.waitForRequest(ENV_BULK_POST);
        await page.locator('.env-section-header .env-save-btn').click();
        const request = await postRequest;
        expect(request.postDataJSON().updates.SCRAPPER_JOBS_SEARCH).toBe('react, python, go');
        await expect(page.locator('.message')).toContainText('Settings saved successfully');
    });

    test('should save scrapper state', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings`);
        await page.locator('.scrapper-editor textarea').fill('{"running": false}');
        const postRequest = page.waitForRequest(SCRAPPER_STATE_POST);
        await page.locator('.scrapper-save-btn').click();
        const request = await postRequest;
        expect(request.postDataJSON().state.running).toBe(false);
        await expect(page.locator('.message')).toContainText('Scrapper state saved successfully');
    });

    test('should show error for invalid scrapper json', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings`);
        await page.locator('.scrapper-editor textarea').fill('{invalid json');
        await page.locator('.scrapper-save-btn').click();
        await expect(page.locator('.message')).toContainText('Invalid JSON format for scrapper state');
    });

    test('should refresh scrapper state', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings`);
        await page.locator('.scrapper-refresh-btn').click();
        await expect(page.locator('.message')).toContainText('Scrapper state refreshed');
    });
});
