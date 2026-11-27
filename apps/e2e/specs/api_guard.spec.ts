import { test, expect } from './coverage.fixtures';
import { BASE_URL, isBlockedApiWrite, setupApiSafetyNet } from './common.helpers';

test.describe('API write guard', () => {
    for (const method of ['POST', 'PUT', 'PATCH', 'DELETE']) {
        test(`blocks ${method} to the API`, () => {
            expect(isBlockedApiWrite(method, `${BASE_URL}/api/filter-configurations`)).toBe(true);
        });
    }

    test('ignores reads and non-API writes', () => {
        expect(isBlockedApiWrite('GET', `${BASE_URL}/api/filter-configurations`)).toBe(false);
        expect(isBlockedApiWrite('POST', `${BASE_URL}/health`)).toBe(false);
    });

    test('stops an unmocked write before it leaves the browser', async ({ browser }) => {
        const context = await browser.newContext();
        const page = await context.newPage();
        const blocked: string[] = [];
        await setupApiSafetyNet(page, write => blocked.push(`${write.method} ${write.url}`));
        await page.route('**/guard-probe', route => route.fulfill({ contentType: 'text/html', body: 'ok' }));
        await page.goto(`${BASE_URL}/guard-probe`);
        const result = await page.evaluate(async () => {
            try {
                await fetch('/api/filter-configurations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
                return 'reached';
            } catch {
                return 'blocked';
            }
        });
        expect(result).toBe('blocked');
        expect(blocked).toEqual([`POST ${BASE_URL}/api/filter-configurations`]);
        await context.close();
    });
});
