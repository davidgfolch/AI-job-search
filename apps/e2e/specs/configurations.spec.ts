import { test, expect } from './coverage.fixtures';
import { Page } from '@playwright/test';
import { BASE_URL, setupPageLogging } from './viewer.helpers';
import { setupConfigurationsMocks, openConfigDropdown, type JobListRequests } from './configurations.helpers';

test.use({
    bypassCSP: true,
});

const CONFIG_PUT = (req: { method(): string; url(): string }) => req.method() === 'PUT' && /\/api\/filter-configurations\/\d+/.test(req.url());
const CONFIG_POST = (req: { method(): string; url(): string }) => req.method() === 'POST' && /\/api\/filter-configurations$/.test(req.url());
const CONFIG_DELETE = (req: { method(): string; url(): string }) => req.method() === 'DELETE' && /\/api\/filter-configurations\/\d+/.test(req.url());

const clickConfig = (page: Page, name: string) =>
    openConfigDropdown(page).then(() => page.locator('.config-suggestion-item').filter({ hasText: name }).locator('.config-name').click());

test.describe('Filter Configurations E2E', () => {
    let jobListRequests: JobListRequests;

    test.beforeEach(async ({ page }) => {
        setupPageLogging(page);
        jobListRequests = await setupConfigurationsMocks(page);
    });

    test('should list configurations in dropdown', async ({ page }) => {
        await page.goto(BASE_URL);
        await openConfigDropdown(page);
        await expect(page.locator('.config-suggestions')).toContainText('Backend Filter');
        await expect(page.locator('.config-suggestions')).toContainText('React Filter');
    });

    test('should load a configuration from dropdown', async ({ page }) => {
        await page.goto(BASE_URL);
        await openConfigDropdown(page);
        await page.locator('.config-suggestion-item').filter({ hasText: 'Backend Filter' }).locator('.config-name').click();
        await expect(page.locator('#job-row-1')).not.toBeVisible();
        await expect(page.locator('#job-row-2')).toBeVisible();
    });

    test('should reload the list when the configuration already in effect is applied again', async ({ page }) => {
        await page.goto(BASE_URL);
        await clickConfig(page, 'Backend Filter');
        await expect(page.locator('#job-row-2')).toBeVisible();

        // The watcher badge reports jobs this configuration has not seen yet, so applying it again has to ask the
        // backend for the page again: the filters are unchanged, so the query key is too and nothing would refetch.
        const backendPageOneRequests = () => jobListRequests.filter(url => {
            const params = new URL(url).searchParams;
            return params.get('search') === 'Backend' && (params.get('page') ?? '1') === '1';
        });
        expect(backendPageOneRequests()).toHaveLength(1);

        await clickConfig(page, 'Backend Filter');

        await expect.poll(() => backendPageOneRequests().length).toBe(2);
        await expect(page.locator('#job-row-2')).toBeVisible();
    });

    test('should not reload the list when a different configuration is applied', async ({ page }) => {
        await page.goto(BASE_URL);
        await clickConfig(page, 'Backend Filter');
        await expect(page.locator('#job-row-2')).toBeVisible();
        const backendRequests = () => jobListRequests.filter(url => new URL(url).searchParams.get('search') === 'Backend').length;
        expect(backendRequests()).toBe(1);

        await clickConfig(page, 'React Filter');
        await expect(page.locator('#job-row-1')).toBeVisible();

        // A different filter set is a different query, so it is fetched once and the previous one is left alone
        expect(jobListRequests.filter(url => new URL(url).searchParams.get('search') === 'React')).toHaveLength(1);
        expect(backendRequests()).toBe(1);
    });

    test('should toggle pin on a configuration', async ({ page }) => {
        await page.goto(BASE_URL);
        await openConfigDropdown(page);
        const putRequest = page.waitForRequest(CONFIG_PUT);
        await page.locator('.config-suggestion-item').filter({ hasText: 'Backend Filter' }).getByTitle('Unpin configuration').click();
        const request = await putRequest;
        expect(request.url()).toContain('/api/filter-configurations/101');
        expect(request.postDataJSON()).toEqual({ pinned: false });
    });

    test('should toggle statistics on a configuration', async ({ page }) => {
        await page.goto(BASE_URL);
        await openConfigDropdown(page);
        const putRequest = page.waitForRequest(CONFIG_PUT);
        await page.locator('.config-suggestion-item').filter({ hasText: 'Backend Filter' }).getByTitle('Exclude from Statistics').click();
        const request = await putRequest;
        expect(request.url()).toContain('/api/filter-configurations/101');
        expect(request.postDataJSON()).toEqual({ statistics: false });
    });

    test('should toggle watch on a configuration', async ({ page }) => {
        await page.goto(BASE_URL);
        await openConfigDropdown(page);
        const putRequest = page.waitForRequest(req => req.method() === 'PUT' && /\/api\/filter-configurations\/102/.test(req.url()));
        await page.locator('.config-suggestion-item').filter({ hasText: 'React Filter' }).getByTitle('Watch').click();
        const request = await putRequest;
        expect(request.postDataJSON().watched).toBe(true);
    });

    test('should delete a configuration', async ({ page }) => {
        await page.goto(BASE_URL);
        await openConfigDropdown(page);
        const deleteRequest = page.waitForRequest(req => req.method() === 'DELETE' && /\/api\/filter-configurations\/101/.test(req.url()));
        await page.locator('.config-suggestion-item').filter({ hasText: 'Backend Filter' }).getByTitle('Delete configuration').click();
        await page.getByRole('button', { name: 'Confirm' }).click();
        const request = await deleteRequest;
        expect(request.url()).toContain('/api/filter-configurations/101');
    });

    test('should save a new configuration', async ({ page }) => {
        await page.goto(BASE_URL);
        const configInput = page.locator('#filter-config-input');
        await configInput.click();
        await configInput.pressSequentially('New Config');
        await expect(configInput).toHaveValue('New Config');
        const postRequest = page.waitForRequest(CONFIG_POST);
        await page.getByTitle('Save current filters with the name above').click();
        const request = await postRequest;
        expect(request.postDataJSON().name).toBe('New Config');
    });
});
