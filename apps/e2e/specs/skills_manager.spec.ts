import { test, expect } from './coverage.fixtures';
import { Page } from '@playwright/test';
import { BASE_URL, setupPageLogging, setupApiSafetyNet, setupAppBootstrapMocks, setupTimezoneMock, setupModalityMock } from './common.helpers';
import { MOCK_SKILLS } from './skills.mocks';

test.use({
    bypassCSP: true,
});

const SKILLS_GET = (req: { method(): string; url(): string }) => req.method() === 'GET' && /\/api\/skills$/.test(req.url());
const SKILLS_POST = (req: { method(): string; url(): string }) => req.method() === 'POST' && /\/api\/skills\/.+/.test(req.url());
const SKILLS_PUT = (req: { method(): string; url(): string }) => req.method() === 'PUT' && /\/api\/skills\/.+/.test(req.url());

async function setupSkillsMocks(page: Page) {
    await setupApiSafetyNet(page);
    await setupAppBootstrapMocks(page);
    await setupTimezoneMock(page);
    await setupModalityMock(page);
    await page.route(/.*\/api\/skills.*/, async (route) => {
        const req = route.request();
        if (req.method() === 'GET') {
            await route.fulfill({ contentType: 'application/json', json: MOCK_SKILLS });
        } else {
            await route.fulfill({ status: 200, contentType: 'application/json', json: 'ok' });
        }
    });
}

test.describe('Skills Manager E2E', () => {
    test.beforeEach(async ({ page }) => {
        setupPageLogging(page);
        await setupSkillsMocks(page);
    });

    test('should display skills table', async ({ page }) => {
        await page.goto(`${BASE_URL}/skills-manager`);
        await expect(page.locator('.skills-table')).toBeVisible();
        await expect(page.locator('.skill-row')).toHaveCount(2);
        await expect(page.locator('.skills-table')).toContainText('React');
        await expect(page.locator('.skills-table')).toContainText('Python');
        await expect(page.locator('.skills-table')).toContainText('https://react.dev');
    });

    test('should toggle between table and markdown views', async ({ page }) => {
        await page.goto(`${BASE_URL}/skills-manager`);
        await page.getByRole('button', { name: 'View MD' }).click();
        await expect(page.locator('.markdown-view')).toBeVisible();
        await expect(page.locator('.markdown-view')).toContainText('My Skills');
        await page.getByRole('button', { name: 'View Table' }).click();
        await expect(page.locator('.skills-table')).toBeVisible();
    });

    test('should export skills to markdown file', async ({ page }) => {
        await page.goto(`${BASE_URL}/skills-manager`);
        const downloadPromise = page.waitForEvent('download');
        await page.getByRole('button', { name: 'Export' }).click();
        const download = await downloadPromise;
        expect(download.suggestedFilename()).toBe('my-skills.md');
    });

    test('should create a new skill', async ({ page }) => {
        await page.goto(`${BASE_URL}/skills-manager`);
        await page.getByRole('button', { name: '+ Add Skill' }).click();
        await expect(page.locator('.modal-content')).toContainText('Add New Skill');
        await page.locator('#skill-name-input').fill('Rust');
        await page.locator('#skill-category-input').fill('Languages');
        await page.locator('#skill-description-textarea').fill('A systems programming language');
        await page.locator('#learning-path-input').fill('https://rust-lang.org');
        await page.getByTitle('Add link').click();
        const postRequest = page.waitForRequest(SKILLS_POST);
        await page.getByRole('button', { name: 'Create Skill' }).click();
        const request = await postRequest;
        expect(request.url()).toContain('/api/skills/Rust');
        expect(request.postDataJSON()).toMatchObject({ name: 'Rust', description: 'A systems programming language' });
    });

    test('should create a new skill with Ctrl+Enter', async ({ page }) => {
        await page.goto(`${BASE_URL}/skills-manager`);
        await page.getByRole('button', { name: '+ Add Skill' }).click();
        await expect(page.locator('.modal-content')).toContainText('Add New Skill');
        await page.locator('#skill-name-input').fill('Rust');
        await page.locator('#skill-category-input').fill('Languages');
        await page.locator('#skill-description-textarea').fill('A systems programming language');
        const postRequest = page.waitForRequest(SKILLS_POST);
        await page.locator('#skill-description-textarea').press('Control+Enter');
        const request = await postRequest;
        expect(request.url()).toContain('/api/skills/Rust');
        expect(request.postDataJSON()).toMatchObject({ name: 'Rust', description: 'A systems programming language' });
    });

    test('should edit an existing skill', async ({ page }) => {
        await page.goto(`${BASE_URL}/skills-manager`);
        await page.locator('.skill-row').filter({ hasText: 'React' }).getByTitle('Edit Skill').click();
        await expect(page.locator('.modal-content')).toContainText('Skill: React');
        await page.getByRole('button', { name: 'Edit', exact: true }).click();
        await page.locator('#skill-description-textarea').fill('Updated React description');
        const putRequest = page.waitForRequest(SKILLS_PUT);
        await page.getByRole('button', { name: 'Save Changes' }).click();
        const request = await putRequest;
        expect(request.url()).toContain('/api/skills/React');
        expect(request.postDataJSON().description).toBe('Updated React description');
    });

    test('should remove a skill with content by disabling it', async ({ page }) => {
        page.on('dialog', dialog => dialog.accept());
        await page.goto(`${BASE_URL}/skills-manager`);
        const putRequest = page.waitForRequest(SKILLS_PUT);
        await page.locator('.skill-row').filter({ hasText: 'Python' }).getByTitle('Remove Skill').click();
        const request = await putRequest;
        expect(request.url()).toContain('/api/skills/Python');
        expect(request.postDataJSON()).toEqual({ disabled: true });
    });
});
