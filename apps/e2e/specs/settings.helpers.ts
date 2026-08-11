import { Page } from '@playwright/test';
import { setupApiSafetyNet, setupAppBootstrapMocks, setupTimezoneMock, setupModalityMock } from './common.helpers';

export const MOCK_ENV_SETTINGS = {
    SCRAPPER_JOBS_SEARCH: 'react, python',
    UI_GROSS_YEAR_URL: 'https://example.com/calculator',
    GLOBAL_TZ: 'Europe/Madrid',
    AI_ENRICHNEW_MODEL: 'Qwen/Qwen2.5-1.5B-Instruct',
};

export const MOCK_SCRAPPER_STATE = {
    running: true,
    platform: 'linkedin',
};

export async function setupSettingsMocks(page: Page) {
    await setupApiSafetyNet(page);
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
    await page.route(/.*\/api\/settings\/scrapper-state.*/, async (route) => {
        if (route.request().method() === 'POST') {
            await route.fulfill({ contentType: 'application/json', json: route.request().postDataJSON().state });
        } else {
            await route.fulfill({ contentType: 'application/json', json: MOCK_SCRAPPER_STATE });
        }
    });
}
