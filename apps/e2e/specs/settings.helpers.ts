import { Page } from '@playwright/test';
import { setupAppBootstrapMocks, setupTimezoneMock, setupModalityMock } from './common.helpers';

export const MOCK_ENV_SETTINGS = {
    SCRAPPER_JOBS_SEARCH: 'react, python',
    UI_GROSS_YEAR_URL: 'https://example.com/calculator',
    GLOBAL_TZ: 'Europe/Madrid',
    AI_ENRICHSKILL_HF_MODEL_ID: 'Qwen/Qwen2.5-1.5B-Instruct',
    AI_ENRICH_LLM_BACKEND: 'ollama',
    AI_ENRICHSKILL_BACKEND: 'ollama',
    AI_FORM_PROVIDER: 'local',
    AI_ENRICH_OLLAMA_MODEL: 'ollama/qwen2.5:3b',
    AI_ENRICHSKILL_OLLAMA_MODEL: 'ollama/qwen2.5:3b',
    AI_FORM_HF_MODEL: 'Qwen/Qwen2.5-1.5B-Instruct',
    OPENAI_API_KEY: 'sk-openai-test',
    OPENROUTER_API_KEY: 'sk-or-test',
};

export const MOCK_SCRAPPER_STATE = {
    running: true,
    platform: 'linkedin',
};

export async function setupSettingsMocks(page: Page) {
    await setupAppBootstrapMocks(page);
    await setupTimezoneMock(page);
    await setupModalityMock(page);
    await page.route(/.*\/api\/settings\/env-bulk.*/, async (route) => {
        await route.fulfill({ contentType: 'application/json', json: route.request().postDataJSON().updates });
    });
    await page.route(/.*\/api\/settings\/env.*/, async (route) => {
        if (route.request().method() === 'POST') {
            const body = route.request().postDataJSON();
            await route.fulfill({ contentType: 'application/json', json: { [body.key]: body.value } });
        } else {
            await route.fulfill({ contentType: 'application/json', json: MOCK_ENV_SETTINGS });
        }
    });
    await page.route(/.*\/api\/settings\/provider-models.*/, async (route) => {
        const provider = new URL(route.request().url()).searchParams.get('provider') ?? '';
        await route.fulfill({ contentType: 'application/json', json: { provider, models: [], source: 'fallback', cached: false, fetched_at: null } });
    });
    await page.route(/.*\/api\/settings\/scrapper-state.*/, async (route) => {
        if (route.request().method() === 'POST') {
            await route.fulfill({ contentType: 'application/json', json: route.request().postDataJSON().state });
        } else {
            await route.fulfill({ contentType: 'application/json', json: MOCK_SCRAPPER_STATE });
        }
    });
}
