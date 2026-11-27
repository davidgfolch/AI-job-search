import { test, expect } from './coverage.fixtures';
import { setupPageLogging, setupSystemMocks, setupDefaultJobsRoute } from './viewer.helpers';
import { ViewerPage } from '../pages/ViewerPage';

test.use({ bypassCSP: true });

test.describe('Viewer mobile panels and edit form', () => {
    let viewer: ViewerPage;

    test.use({ viewport: { width: 375, height: 800 } });

    test.beforeEach(async ({ page }) => {
        viewer = new ViewerPage(page);
        setupPageLogging(page);
        await setupSystemMocks(page);
        await setupDefaultJobsRoute(page);
        await viewer.open();
    });

    test('allows editing the selected job fields', async ({ page }) => {
        await viewer.selectJob(1);
        await viewer.editTab.click();
        await expect(page.locator('#viewer-left')).toBeVisible();
        const form = page.locator('.job-edit-form:visible');
        await expect(form).toBeVisible();
        const clientInput = form.locator('input[name="client"]');
        await expect(clientInput).toBeVisible();
        await clientInput.fill('Updated client');
        await expect(clientInput).toHaveValue('Updated client');
    });

    test('can scroll the edit form on a small screen', async ({ page }) => {
        await viewer.selectJob(1);
        await viewer.editTab.click();
        await page.getByRole('button', { name: 'Edit All' }).click();
        const form = page.locator('.job-edit-form:visible');
        await expect(form).toBeVisible();
        const scrolled = await form.evaluate((element) => {
            const before = element.scrollTop;
            element.scrollTop = element.scrollHeight;
            return { before, after: element.scrollTop, max: element.scrollHeight - element.clientHeight };
        });
        expect(scrolled.max).toBeGreaterThan(0);
        expect(scrolled.after).toBeGreaterThan(scrolled.before);
    });

    test('uses compact status pills on a small screen', async ({ page }) => {
        await viewer.createTab.click();
        const pill = page.locator('.status-pill').first();
        const style = await pill.evaluate((element) => {
            const computed = getComputedStyle(element);
            return { paddingTop: parseFloat(computed.paddingTop), paddingLeft: parseFloat(computed.paddingLeft) };
        });
        expect(style.paddingTop).toBeLessThanOrEqual(6);
        expect(style.paddingLeft).toBeLessThanOrEqual(10);
    });

    test('switches between detail and edit views through the tabs', async () => {
        await viewer.selectJob(1);
        await expect(viewer.detailPanel).toBeVisible();
        await viewer.editTab.click();
        await expect(viewer.detailPanel).toBeHidden();
        await expect(viewer.editTab).toHaveClass(/active/);
        await viewer.listTab.click();
        await expect(viewer.detailPanel).toBeVisible();
    });

    test('shows the create view from the tab strip while a job is selected', async () => {
        await viewer.selectJob(1);
        await viewer.createTab.click();
        await expect(viewer.detailPanel).toBeHidden();
        await expect(viewer.tabButtons).toBeVisible();
    });
});
