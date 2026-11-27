import { test, expect } from './coverage.fixtures';
import { setupPageLogging, setupSystemMocks, setupDefaultJobsRoute } from './viewer.helpers';
import { ViewerPage } from '../pages/ViewerPage';

test.use({ bypassCSP: true, viewport: { width: 2200, height: 900 } });

test.describe('Viewer list and detail panels', () => {
    let viewer: ViewerPage;

    test.beforeEach(async ({ page }) => {
        viewer = new ViewerPage(page);
        setupPageLogging(page);
        await setupSystemMocks(page);
        await setupDefaultJobsRoute(page);
        await viewer.open();
    });

    test('shows location and modality right after company', async () => {
        await expect(viewer.locationHeader).toBeVisible();
        await expect(viewer.modalityHeader).toBeVisible();
        expect(await viewer.headers.allTextContents()).toEqual(['', 'Salary', 'Title', 'Company', 'Location', 'Modality', 'Status', 'Created']);
        await expect(viewer.locationCell(1)).toHaveText('Remote');
        await expect(viewer.modalityBadges(1)).toHaveText(['R', 'H']);
        await expect(viewer.modalityBadges(1).first()).toHaveAttribute('title', 'REMOTE');
        await expect(viewer.modalityBadges(2)).toHaveText(['O']);
    });

    test('toggles the list off and back on without losing the divider', async () => {
        await viewer.collapseListButton.click();
        await expect(viewer.jobRow(1)).toBeHidden();
        await expect(viewer.divider).toBeVisible();
        await expect(viewer.collapseListButton).toBeVisible();
        await expect(viewer.collapseListButton).toHaveAttribute('aria-pressed', 'true');
        await viewer.collapseListButton.click();
        await expect(viewer.jobRow(1)).toBeVisible();
        await expect(viewer.collapseListButton).toHaveAttribute('aria-pressed', 'false');
        await expect(viewer.resetButton).toHaveCount(0);
    });

    test('toggles the detail off and back on without losing the divider', async () => {
        await viewer.selectJob(1);
        await expect(viewer.detailTitle).toBeVisible();
        await viewer.collapseDetailButton.click();
        await expect(viewer.detailTitle).toBeHidden();
        await expect(viewer.divider).toBeVisible();
        await expect(viewer.collapseDetailButton).toBeVisible();
        await expect(viewer.collapseDetailButton).toHaveAttribute('aria-pressed', 'true');
        await viewer.collapseDetailButton.click();
        await expect(viewer.detailTitle).toBeVisible();
        await expect(viewer.collapseDetailButton).toHaveAttribute('aria-pressed', 'false');
    });

    test('resizes with the keyboard, persists the split and resets it', async ({ page }) => {
        await viewer.resizeHandle.focus();
        await expect(viewer.resizeHandle).toHaveAttribute('aria-valuenow', '50');
        await page.keyboard.press('ArrowRight');
        await expect(viewer.resizeHandle).toHaveAttribute('aria-valuenow', '52');
        expect(await viewer.storedRatio()).toBe('0.52');
        await page.reload();
        await viewer.jobRow(1).waitFor();
        await expect(viewer.resizeHandle).toHaveAttribute('aria-valuenow', '52');
        await viewer.collapseDetailButton.click();
        await viewer.resetButton.click();
        await expect(viewer.divider).toBeVisible();
        await expect(viewer.resizeHandle).toHaveAttribute('aria-valuenow', '50');
        expect(await viewer.storedRatio()).toBe('0.5');
    });
});
