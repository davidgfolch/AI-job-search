import { Page } from '@playwright/test';

export const BASE_URL = 'http://127.0.0.1:5173';

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
