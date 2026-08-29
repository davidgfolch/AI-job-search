import { test, expect } from './coverage.fixtures';
import { Page } from '@playwright/test';
import { BASE_URL, setupPageLogging, setupApiSafetyNet, setupAppBootstrapMocks, setupTimezoneMock, setupModalityMock } from './common.helpers';

test.use({
    bypassCSP: true,
});

async function setupSynonymsMocks(page: Page) {
    await setupApiSafetyNet(page);
    await setupAppBootstrapMocks(page);
    await setupTimezoneMock(page);
    await setupModalityMock(page);
    await page.route(/.*\/api\/company-synonyms.*/, async (route) => {
        const req = route.request();
        if (req.method() === 'GET') {
            await route.fulfill({ contentType: 'application/json', json: [] });
        } else {
            await route.fulfill({ status: 200, contentType: 'application/json', json: { group_id: 1 } });
        }
    });
}

test.describe('Company Synonyms E2E', () => {
    test.beforeEach(async ({ page }) => {
        setupPageLogging(page);
        await setupSynonymsMocks(page);
    });

    test('should display the company synonyms page', async ({ page }) => {
        await page.goto(`${BASE_URL}/company-synonyms`);
        await expect(page.getByRole('button', { name: '+ Add Synonym Group' })).toBeVisible();
    });

    test('should create a synonym group when Enter is pressed', async ({ page }) => {
        await page.goto(`${BASE_URL}/company-synonyms`);
        await page.getByRole('button', { name: '+ Add Synonym Group' }).click();
        await expect(page.getByText('New Synonym Group')).toBeVisible();
        const inputs = page.locator('input.form-input');
        await inputs.nth(0).fill('Acme');
        await inputs.nth(1).fill('Acme Inc');
        const postRequest = page.waitForRequest(req => req.method() === 'POST' && /\/api\/company-synonyms\/groups/.test(req.url()));
        await page.keyboard.press('Enter');
        const request = await postRequest;
        expect(request.postDataJSON()).toEqual({ names: ['Acme', 'Acme Inc'] });
        await expect(page.getByText('New Synonym Group')).not.toBeVisible();
    });

    test('should close the create modal with Escape', async ({ page }) => {
        await page.goto(`${BASE_URL}/company-synonyms`);
        await page.getByRole('button', { name: '+ Add Synonym Group' }).click();
        await expect(page.getByText('New Synonym Group')).toBeVisible();
        await page.keyboard.press('Escape');
        await expect(page.getByText('New Synonym Group')).not.toBeVisible();
    });
});
