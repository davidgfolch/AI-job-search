import { Page } from '@playwright/test';

export const BASE_URL = 'http://127.0.0.1:5174';

export async function setupPageLogging(page: Page) {
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
    page.on('requestfailed', request => console.log('REQUEST FAILED:', request.url(), request.failure()?.errorText));
}

export async function setupTimezoneMock(page: Page) {
    await page.route(/.*\/api\/system\/timezone.*/, async (route) => {
        await route.fulfill({
            contentType: 'application/json',
            json: { offset_minutes: 0 }
        });
    });
}

export async function setupModalityMock(page: Page) {
    await page.route(/.*\/api\/ddl\/schema\/enum-values.*/, async (route) => {
        await route.fulfill({
            contentType: 'application/json',
            json: ['REMOTE', 'HYBRID', 'ON_SITE']
        });
    });
}

export async function setupSalaryHistoryMocks(page: Page) {
    await page.route(/.*\/api\/jobs\/history\/by-company.*/, async (route) => {
        await route.fulfill({ contentType: 'application/json', json: [] });
    });
    await page.route(/.*\/api\/jobs\/\d+\/history.*/, async (route) => {
        await route.fulfill({ contentType: 'application/json', json: [] });
    });
}

export async function setupAppBootstrapMocks(page: Page) {
    await page.route(/.*\/api\/settings\/env.*/, async (route) => {
        await route.fulfill({ contentType: 'application/json', json: {} });
    });
    await page.route(/.*\/api\/skills.*/, async (route) => {
        await route.fulfill({ contentType: 'application/json', json: [] });
    });
}

export async function setupApiSafetyNet(page: Page) {
    await page.route(/^https?:\/\/[^/]+\/api\//, async (route) => {
        console.log('UNMOCKED API REQUEST:', route.request().url());
        await route.fulfill({ status: 404, contentType: 'application/json', json: {} });
    });
}
