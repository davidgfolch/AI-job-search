import { test, expect } from './coverage.fixtures';
import { BASE_URL, setupPageLogging } from './viewer.helpers';
import { setupSettingsMocks } from './settings.helpers';

test.use({
    bypassCSP: true,
});

const ENV_BULK_POST = (req: { method(): string; url(): string }) => req.method() === 'POST' && /\/api\/settings\/env-bulk/.test(req.url());
const ENV_SINGLE_POST = (req: { method(): string; url(): string }) => req.method() === 'POST' && /\/api\/settings\/env(\?|$)/.test(req.url());
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

    test('should switch each LLM provider independently', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings`);
        await expect(page.locator('#llm-provider-AI_ENRICH_LLM_BACKEND')).toHaveValue('ollama');
        await expect(page.locator('#llm-provider-AI_ENRICHSKILL_BACKEND')).toHaveValue('ollama');
        await expect(page.locator('#llm-provider-AI_FORM_PROVIDER')).toHaveValue('local');

        const firstPost = page.waitForRequest(ENV_SINGLE_POST);
        await page.locator('#llm-provider-AI_ENRICH_LLM_BACKEND').selectOption('openrouter');
        expect((await firstPost).postDataJSON()).toEqual({ key: 'AI_ENRICH_LLM_BACKEND', value: 'openrouter' });
        await expect(page.locator('#llm-provider-AI_ENRICHSKILL_BACKEND')).toHaveValue('ollama');

        const secondPost = page.waitForRequest(ENV_SINGLE_POST);
        await page.locator('#llm-provider-AI_ENRICHSKILL_BACKEND').selectOption('huggingface');
        expect((await secondPost).postDataJSON()).toEqual({ key: 'AI_ENRICHSKILL_BACKEND', value: 'huggingface' });
        await expect(page.locator('#llm-provider-AI_ENRICH_LLM_BACKEND')).toHaveValue('openrouter');

        const thirdPost = page.waitForRequest(ENV_SINGLE_POST);
        await page.locator('#llm-provider-AI_FORM_PROVIDER').selectOption('openai');
        expect((await thirdPost).postDataJSON()).toEqual({ key: 'AI_FORM_PROVIDER', value: 'openai' });
        await expect(page.locator('#llm-provider-AI_ENRICH_LLM_BACKEND')).toHaveValue('openrouter');
        await expect(page.locator('#llm-provider-AI_ENRICHSKILL_BACKEND')).toHaveValue('huggingface');
        await expect(page.locator('.message')).toContainText('AI_FORM_PROVIDER switched to openai');
    });

    test('should group provider fields with the selectors', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings`);
        await expect(page.locator('.llm-providers-section #env-OPENAI_API_KEY')).toHaveValue('sk-openai-test');
        await expect(page.locator('.llm-providers-section #env-OPENROUTER_API_KEY')).toHaveValue('sk-or-test');
        await expect(page.locator('.llm-provider-group:has(#llm-provider-AI_FORM_PROVIDER) #env-OPENAI_API_KEY')).toHaveValue('sk-openai-test');
        await expect(page.locator('.llm-provider-group:has(#llm-provider-AI_FORM_PROVIDER) #env-OPENROUTER_MODEL')).toHaveValue('openai/gpt-4o-mini');
        await expect(page.locator('.llm-provider-group:has(#llm-provider-AI_ENRICH_LLM_BACKEND) #env-OPENAI_API_KEY')).toHaveCount(0);
        await expect(page.locator('.env-variables-section #env-OPENAI_API_KEY')).toHaveCount(0);
        await expect(page.locator('.env-variables-section #env-OPENROUTER_API_KEY')).toHaveCount(0);
        await expect(page.locator('.env-variables-section #env-OPENROUTER_MODEL')).toHaveCount(0);
    });

    test('should save the OpenAI API key from the provider section', async ({ page }) => {
        await page.goto(`${BASE_URL}/settings`);
        await page.locator('#env-OPENAI_API_KEY').fill('sk-new-key');
        const postRequest = page.waitForRequest(ENV_BULK_POST);
        await page.locator('.env-section-footer .env-save-btn').click();
        expect((await postRequest).postDataJSON().updates.OPENAI_API_KEY).toBe('sk-new-key');
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
