import { Page } from '@playwright/test';
import { MOCK_JOB_1, MOCK_JOBS_LIST, MOCK_SEARCH_BACKEND } from './viewer.mocks';
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

export async function setupConfigurationsMocks(page: Page): Promise<JobListRequests> {
    await setupApiSafetyNet(page);
    await setupAppBootstrapMocks(page);
    await setupTimezoneMock(page);
    await setupModalityMock(page);
    await setupSalaryHistoryMocks(page);
    const jobListRequests = await setupConfigurationsJobsRoute(page);
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
    return jobListRequests;
}

export async function openConfigDropdown(page: Page) {
    await page.locator('#filter-config-input').click();
    await page.locator('.config-suggestions').waitFor({ state: 'visible' });
}

/** Records every job list request, so a spec can tell a refetch from the query cache serving the same page. */
export type JobListRequests = string[];

export async function setupConfigurationsJobsRoute(page: Page): Promise<JobListRequests> {
    const jobListRequests: JobListRequests = [];
    await page.route(/.*\/api\/jobs.*/, async (route) => {
        const url = route.request().url();
        if (url.includes('/applied-by-company')) {
            await route.fulfill({ json: [] });
            return;
        }
        if (/\/api\/jobs\/\d+$/.test(url)) {
            await route.fulfill({ json: MOCK_JOB_1 });
            return;
        }
        if (url.includes('/history')) {
            await route.fulfill({ json: [] });
            return;
        }
        if (/\/api\/jobs(\?|$)/.test(url)) {
            jobListRequests.push(url);
            const search = new URL(url).searchParams.get('search');
            await route.fulfill({ json: search === 'Backend' ? MOCK_SEARCH_BACKEND : MOCK_JOBS_LIST });
            return;
        }
        await route.fallback();
    });
    return jobListRequests;
}
