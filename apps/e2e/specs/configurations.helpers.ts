import { Page } from '@playwright/test';
import { setupDefaultJobsRoute } from './viewer.helpers';
import { setupApiSafetyNet, setupAppBootstrapMocks, setupTimezoneMock, setupModalityMock, setupSalaryHistoryMocks } from './common.helpers';

export const MOCK_FILTER_CONFIGS = [
    {
        id: 101,
        name: 'Backend Filter',
        filters: { search: 'Backend', page: 1, size: 20 },
        pinned: true,
        statistics: true,
        watched: false,
        ordering: 0,
        created: '2023-01-01',
        modified: null,
    },
    {
        id: 102,
        name: 'React Filter',
        filters: { search: 'React', page: 1, size: 20 },
        pinned: false,
        statistics: false,
        watched: false,
        ordering: 1,
        created: '2023-01-01',
        modified: null,
    },
];

export async function setupConfigurationsMocks(page: Page) {
    await setupApiSafetyNet(page);
    await setupAppBootstrapMocks(page);
    await setupTimezoneMock(page);
    await setupModalityMock(page);
    await setupSalaryHistoryMocks(page);
    await setupDefaultJobsRoute(page);
    await page.route(/.*\/api\/filter-configurations.*/, async (route) => {
        const req = route.request();
        const method = req.method();
        if (method === 'GET') {
            await route.fulfill({ contentType: 'application/json', json: MOCK_FILTER_CONFIGS });
            return;
        }
        if (method === 'POST') {
            await route.fulfill({ status: 201, contentType: 'application/json', json: { ...req.postDataJSON(), id: 103 } });
            return;
        }
        if (method === 'PUT') {
            const id = Number(req.url().split('/').pop());
            await route.fulfill({ status: 200, contentType: 'application/json', json: { id, ...req.postDataJSON() } });
            return;
        }
        if (method === 'DELETE') {
            await route.fulfill({ status: 200, contentType: 'application/json', json: {} });
            return;
        }
        await route.fulfill({ status: 404, contentType: 'application/json', json: {} });
    });
    await page.route(/.*\/api\/jobs\/watcher-stats.*/, async (route) => {
        await route.fulfill({ contentType: 'application/json', json: {} });
    });
}

export async function openConfigDropdown(page: Page) {
    await page.locator('#filter-config-input').click();
    await page.locator('.config-suggestions').waitFor({ state: 'visible' });
}
