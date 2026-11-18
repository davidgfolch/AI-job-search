import { test, expect } from './coverage.fixtures';
import { setupPageLogging, setupSystemMocks, setupDefaultJobsRoute } from './viewer.helpers';
import { ViewerPage } from '../pages/ViewerPage';

test.use({ bypassCSP: true });

test.describe('Viewer tab buttons below 844px', () => {
    let viewer: ViewerPage;

    test.use({ viewport: { width: 843, height: 900 } });

    test.beforeEach(async ({ page }) => {
        viewer = new ViewerPage(page);
        setupPageLogging(page);
        await setupSystemMocks(page);
        await setupDefaultJobsRoute(page);
        await viewer.open();
    });

    test('shows icons instead of labels and keeps the strip visible', async () => {
        await expect(viewer.tabButtons).toBeVisible();
        await expect(viewer.listTab.locator('.tab-icon')).toBeVisible();
        await expect(viewer.listTab.locator('.tab-label')).toBeHidden();
        await viewer.selectJob(1);
        await expect(viewer.detailTitle).toBeVisible();
        await expect(viewer.tabButtons).toBeVisible();
    });

    test('uses compact, uniform tab button spacing', async () => {
        const metrics = await viewer.listTab.evaluate((element) => {
            const row = element.parentElement!;
            const buttons = Array.from(row.querySelectorAll<HTMLElement>('.tab-button'));
            const rowStyle = getComputedStyle(row);
            return {
                heights: buttons.map((button) => Math.round(button.getBoundingClientRect().height)),
                paddings: buttons.map((button) => parseFloat(getComputedStyle(button).paddingTop)),
                rowGap: parseFloat(rowStyle.gap),
                rowPadding: parseFloat(rowStyle.paddingTop)
            };
        });
        expect(new Set(metrics.heights).size).toBe(1);
        expect(metrics.paddings.every((padding) => padding <= 6)).toBe(true);
        expect(metrics.rowGap).toBeLessThanOrEqual(4);
        expect(metrics.rowPadding).toBeLessThanOrEqual(4);
    });
});

test.describe('Viewer tab buttons at 844px and above', () => {
    let viewer: ViewerPage;

    test.use({ viewport: { width: 844, height: 900 } });

    test.beforeEach(async ({ page }) => {
        viewer = new ViewerPage(page);
        setupPageLogging(page);
        await setupSystemMocks(page);
        await setupDefaultJobsRoute(page);
        await viewer.open();
    });

    test('shows labels instead of icon-only tabs', async () => {
        await expect(viewer.tabButtons).toBeVisible();
        await expect(viewer.listTab.locator('.tab-label')).toBeVisible();
        await expect(viewer.editTab.locator('.tab-label')).toBeVisible();
        await expect(viewer.createTab.locator('.tab-label')).toBeVisible();
    });
});

test.describe('Viewer tab buttons on small screens', () => {
    let viewer: ViewerPage;

    test.use({ viewport: { width: 375, height: 800 } });

    test.beforeEach(async ({ page }) => {
        viewer = new ViewerPage(page);
        setupPageLogging(page);
        await setupSystemMocks(page);
        await setupDefaultJobsRoute(page);
        await viewer.open();
    });

    test('keeps the tab strip visible in both list and detail views', async () => {
        await expect(viewer.tabButtons).toBeVisible();
        await expect(viewer.jobRow(1)).toBeVisible();
        await viewer.selectJob(1);
        await expect(viewer.detailTitle).toBeVisible();
        await expect(viewer.tabButtons).toBeVisible();
    });

    test('hides the panel divider and collapse controls', async () => {
        await expect(viewer.divider).toBeHidden();
        await expect(viewer.collapseListButton).toBeHidden();
        await expect(viewer.collapseDetailButton).toBeHidden();
    });

    test('hides the status column', async ({ page }) => {
        await expect(page.locator('#job-table .status-column').first()).toBeHidden();
    });

    test('uses one uniform gap between tab buttons', async () => {
        const gaps = await viewer.tabButtons.evaluate((row) => {
            const buttons = Array.from(row.querySelectorAll<HTMLElement>('.tab-button'));
            return buttons.slice(1).map((button, index) => Math.round(button.getBoundingClientRect().left - buttons[index].getBoundingClientRect().right));
        });
        expect(new Set(gaps).size).toBe(1);
    });

    test('uses uniform margins and heights for every toolbar button', async () => {
        await viewer.selectJob(1);
        const metrics = await viewer.tabButtons.evaluate((row) => {
            const buttons = Array.from(row.querySelectorAll<HTMLElement>('.tab-button, .list-header-actions .header-button'));
            return buttons.map((button) => {
                const style = getComputedStyle(button);
                return { marginTop: parseFloat(style.marginTop), marginLeft: parseFloat(style.marginLeft), height: Math.round(button.getBoundingClientRect().height) };
            });
        });
        expect(metrics.length).toBeGreaterThan(1);
        expect(metrics.every((metric) => metric.marginTop === 0 && metric.marginLeft === 0)).toBe(true);
        expect(new Set(metrics.map((metric) => metric.height)).size).toBe(1);
    });

    test('floats action buttons as individual items without overflowing the toolbar', async () => {
        await viewer.selectJob(1);
        const layout = await viewer.tabButtons.evaluate((row) => {
            const wrapper = row.querySelector<HTMLElement>('.list-header-actions')!;
            const buttons = Array.from(row.querySelectorAll<HTMLElement>('.tab-button, .header-button'));
            return {
                wrapperDisplay: getComputedStyle(wrapper).display,
                buttonCount: buttons.length,
                noHorizontalOverflow: row.scrollWidth <= row.clientWidth + 1,
                separatorHidden: getComputedStyle(row.querySelector<HTMLElement>('.button-separator')!).display === 'none'
            };
        });
        expect(layout.wrapperDisplay).toBe('contents');
        expect(layout.buttonCount).toBeGreaterThan(8);
        expect(layout.noHorizontalOverflow).toBe(true);
        expect(layout.separatorHidden).toBe(true);
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

    test('shows icons instead of labels at small widths', async () => {
        await expect(viewer.listTab.locator('.tab-icon')).toBeVisible();
        await expect(viewer.listTab.locator('.tab-label')).toBeHidden();
    });

    test('keeps shortcut badges and keyboard actions working with the flattened toolbar', async ({ page }) => {
        await viewer.selectJob(1);
        await expect(viewer.detailTitle).toContainText('Frontend Engineer');
        await page.keyboard.down('Alt');
        await expect(viewer.tabButtons.locator('.shortcut-badge').filter({ hasText: 'Alt+I' })).toBeVisible();
        await expect(viewer.tabButtons.locator('.shortcut-badge').filter({ hasText: 'Alt+N' })).toBeVisible();
        await page.keyboard.up('Alt');
        await page.keyboard.press('Alt+n');
        await expect(viewer.detailTitle).toContainText('Backend Developer');
    });

    test('keeps every action button in the toolbar in detail-only view', async ({ page }) => {
        await viewer.selectJob(1);
        await expect(viewer.detailTitle).toBeVisible();
        await expect(viewer.tabButtons.locator('.list-header-actions')).toBeVisible();
        await expect(page.locator('.mobile-job-actions')).toHaveCount(0);
        const closeButton = viewer.tabButtons.locator('#detail-close-button');
        await expect(closeButton).toBeVisible();
        await closeButton.click();
        await expect(viewer.detailTitle).toBeHidden();
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
