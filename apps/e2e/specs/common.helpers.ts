import { Page } from '@playwright/test';

export const BASE_URL = 'http://127.0.0.1:5174';

export async function setupPageLogging(page: Page) {
    // Only surface warnings and errors; skip noisy info/debug/log chatter.
    page.on('console', msg => {
        const type = msg.type();
        if (type === 'warning' || type === 'error') {
            console.log(`PAGE ${type.toUpperCase()}:`, msg.text());
        }
    });
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

const MUTATING_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

export function isBlockedApiWrite(method: string, url: string): boolean {
    return MUTATING_METHODS.includes(method.toUpperCase()) && /^https?:\/\/[^/]+\/api\//.test(url);
}

export type BlockedWrite = { method: string; url: string };

export async function setupApiSafetyNet(page: Page, onBlocked?: (write: BlockedWrite) => void) {
    await page.route(/^https?:\/\/[^/]+\/api\//, async (route) => {
        const request = route.request();
        const method = request.method();
        const url = request.url();
        if (isBlockedApiWrite(method, url)) {
            if (!onBlocked) {
                throw new Error(`Blocked unmocked E2E write: ${method} ${url}. Add an explicit route mock in the spec.`);
            }
            onBlocked({ method, url });
            await route.abort();
            return;
        }
        await route.fulfill({ status: 404, contentType: 'application/json', json: {} });
    });
}
