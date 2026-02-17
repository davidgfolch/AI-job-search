import { Page } from '@playwright/test';
import { MOCK_JOB_1, MOCK_JOB_2, MOCK_JOBS_LIST, MOCK_SEARCH_BACKEND } from './viewer.mocks';
import { BASE_URL, setupPageLogging, setupTimezoneMock } from './common.helpers';

export { BASE_URL, setupPageLogging, setupTimezoneMock };

export async function setupSystemMocks(page: Page) {
    await setupTimezoneMock(page);
    await page.route(/.*\/api\/filter-configurations.*/, async (route) => {
        await route.fulfill({
            contentType: 'application/json',
            json: []
        });
    });
}

export async function setupDefaultJobsRoute(page: Page) {
    await page.route(/.*\/api\/jobs.*/, async (route) => {
        const url = route.request().url();
        console.log('MOCKING REQUEST:', url);
        if (url.includes('/applied-by-company')) {
            await route.fulfill({ json: [] });
            return;
        }
        if (/\/api\/jobs\/\d+$/.test(url)) {
            await route.fulfill({ json: MOCK_JOB_1 });
            return;
        }
        const searchParam = new URL(url).searchParams.get('search');
        if (searchParam === 'Backend') {
            console.log('REPLYING WITH BACKEND SEARCH RESULTS');
            await route.fulfill({ json: MOCK_SEARCH_BACKEND });
            return;
        }
        if (/\/api\/jobs(\?|$)/.test(url)) {
            console.log('REPLYING WITH DEFAULT JOB LIST');
            await route.fulfill({ json: MOCK_JOBS_LIST });
            return;
        }
        console.log('UNHANDLED REQUEST:', url);
        route.continue();
    });
}

export async function setupStateChangeJobsRoute(page: Page) {
    let listRequestCount = 0;
    await page.route(/.*\/api\/jobs.*/, async (route) => {
        const url = route.request().url();
        if (url.includes('/applied-by-company')) {
            await route.fulfill({ json: [] });
            return;
        }
        if (/\/api\/jobs\/\d+$/.test(url)) {
            const jobId = url.split('/').pop();
            if (jobId === '1') await route.fulfill({ json: MOCK_JOB_1 });
            if (jobId === '2') await route.fulfill({ json: MOCK_JOB_2 });
            return;
        }
        if (/\/api\/jobs(\?|$)/.test(url)) {
            listRequestCount++;
            if (listRequestCount === 1) {
                await route.fulfill({ json: MOCK_JOBS_LIST });
            } else {
                await route.fulfill({ 
                    json: { 
                        ...MOCK_JOBS_LIST, 
                        items: [MOCK_JOB_2], 
                        total: 1 
                    } 
                });
            }
            return;
        }
        await route.continue();
    });
}

export async function setupJobUpdateRoute(page: Page) {
    await page.route(/.*\/api\/jobs\/1/, async (route) => {
        if (route.request().method() === 'PATCH') {
            await route.fulfill({ json: { ...MOCK_JOB_1, applied: true } });
        } else {
            await route.continue();
        }
    });
}

export async function toggleFiltersIfNeeded(page: Page) {
    const filterContent = page.locator('.filters-content');
    const isExpanded = await filterContent.count() > 0;
    if (!isExpanded) {
        await page.locator('#toggle-filters').click({ force: true });
        await filterContent.waitFor({ state: 'visible', timeout: 10000 });
    }
    await page.locator('#filter-search').waitFor({ state: 'visible', timeout: 10000 });
}

export async function waitForFilterConfigurations(page: Page) {
    await page.waitForResponse(resp => resp.url().includes('api/filter-configurations') && resp.status() === 200);
}

export async function searchJobs(page: Page, searchTerm: string) {
    const responsePromise = page.waitForResponse(resp => 
        resp.url().includes(`search=${searchTerm}`) && resp.status() === 200
    );
    await page.locator('#filter-search').fill(searchTerm);
    await responsePromise;
}
