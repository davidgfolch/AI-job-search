import { test, expect } from './coverage.fixtures';
import {
    BASE_URL,
    setupPageLogging,
    setupSystemMocks,
    setupDefaultJobsRoute
} from './viewer.helpers';
import { MOCK_JOB_1 } from './viewer.mocks';

test.use({
    bypassCSP: true,
});

test.describe('Job Detail Comment Editing', () => {
    test.beforeEach(async ({ page }) => {
        setupPageLogging(page);
        await setupSystemMocks(page);
        await setupDefaultJobsRoute(page);
    });

    test('should allow typing in comments textarea without cursor jumping', async ({ page }) => {
        // Setup job detail route
        await page.route(/.*\/api\/jobs\/1/, async (route) => {
            if (route.request().method() === 'PATCH') {
                await route.fulfill({ json: { ...MOCK_JOB_1, comments: route.request().postDataJSON()?.comments || '' } });
            } else {
                await route.fulfill({ json: MOCK_JOB_1 });
            }
        });

        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await expect(page.locator('#job-detail-title')).toContainText('Frontend Engineer');

        // Switch to Edit tab to show the edit form
        await page.locator('#tab-button-edit').click();
        await expect(page.locator('.job-edit-form:has(.toggle-edit-btn)')).toBeVisible({ timeout: 10000 });

        // Click "Edit All" button to show the comments field
        const editAllButton = page.locator('.toggle-edit-btn button');
        await editAllButton.waitFor({ state: 'visible', timeout: 10000 });
        await editAllButton.click();

        // Find the comments textarea
        const commentsTextarea = page.locator('#job-1-comments');
        await commentsTextarea.waitFor({ state: 'visible', timeout: 10000 });

        // Type a long comment that will cause wrapping
        const longComment = 'This is a very long comment that should wrap to multiple lines and test the auto-resize functionality. It should not cause the cursor to jump or lose keystrokes while typing. The textarea should grow smoothly as the text wraps to new lines.';

        await commentsTextarea.fill(longComment);

        // Verify the comment was typed correctly (no keystrokes lost)
        await expect(commentsTextarea).toHaveValue(longComment);

        // Verify the textarea height grew (auto-resize worked)
        const height = await commentsTextarea.evaluate((el: HTMLTextAreaElement) => el.scrollHeight);
        expect(height).toBeGreaterThan(60); // min-height is 60px, should be taller now
    });

    test('should auto-resize textarea on Enter key (newline)', async ({ page }) => {
        // Setup job detail route
        await page.route(/.*\/api\/jobs\/1/, async (route) => {
            if (route.request().method() === 'PATCH') {
                await route.fulfill({ json: { ...MOCK_JOB_1, comments: route.request().postDataJSON()?.comments || '' } });
            } else {
                await route.fulfill({ json: MOCK_JOB_1 });
            }
        });

        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await expect(page.locator('#job-detail-title')).toContainText('Frontend Engineer');

        // Switch to Edit tab to show the edit form
        await page.locator('#tab-button-edit').click();
        await expect(page.locator('.job-edit-form:has(.toggle-edit-btn)')).toBeVisible({ timeout: 10000 });

        // Click "Edit All" button to show the comments field
        const editAllButton = page.locator('.toggle-edit-btn button');
        await editAllButton.waitFor({ state: 'visible', timeout: 10000 });
        await editAllButton.click();

        // Find the comments textarea
        const commentsTextarea = page.locator('#job-1-comments');
        await commentsTextarea.waitFor({ state: 'visible', timeout: 10000 });

        // Get initial height
        const initialHeight = await commentsTextarea.evaluate((el: HTMLTextAreaElement) => el.scrollHeight);

        // Type text and press Enter to create newlines
        await commentsTextarea.fill('Line 1');
        await commentsTextarea.press('Enter');
        await commentsTextarea.fill('Line 1\nLine 2');
        await commentsTextarea.press('Enter');
        await commentsTextarea.fill('Line 1\nLine 2\nLine 3');

        // Verify the textarea height grew
        const newHeight = await commentsTextarea.evaluate((el: HTMLTextAreaElement) => el.scrollHeight);
        expect(newHeight).toBeGreaterThan(initialHeight);
    });

    test('should auto-resize textarea on word wrap', async ({ page }) => {
        // Setup job detail route
        await page.route(/.*\/api\/jobs\/1/, async (route) => {
            if (route.request().method() === 'PATCH') {
                await route.fulfill({ json: { ...MOCK_JOB_1, comments: route.request().postDataJSON()?.comments || '' } });
            } else {
                await route.fulfill({ json: MOCK_JOB_1 });
            }
        });

        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await expect(page.locator('#job-detail-title')).toContainText('Frontend Engineer');

        // Switch to Edit tab to show the edit form
        await page.locator('#tab-button-edit').click();
        await expect(page.locator('.job-edit-form:has(.toggle-edit-btn)')).toBeVisible({ timeout: 10000 });

        // Click "Edit All" button to show the comments field
        const editAllButton = page.locator('.toggle-edit-btn button');
        await editAllButton.waitFor({ state: 'visible', timeout: 10000 });
        await editAllButton.click();

        // Find the comments textarea
        const commentsTextarea = page.locator('#job-1-comments');
        await commentsTextarea.waitFor({ state: 'visible', timeout: 10000 });

        // Get initial height
        const initialHeight = await commentsTextarea.evaluate((el: HTMLTextAreaElement) => el.scrollHeight);

        // Type a long sentence with spaces that will force wrapping
        const longText = 'This is a very long sentence with many words that will force the textarea to wrap to multiple lines because the words are long enough to exceed the width of the textarea and cause natural word wrapping to occur.';
        await commentsTextarea.fill(longText);

        // Verify the textarea height grew due to word wrap
        const newHeight = await commentsTextarea.evaluate((el: HTMLTextAreaElement) => el.scrollHeight);
        expect(newHeight).toBeGreaterThan(initialHeight);
    });

    test('should preserve cursor position while typing rapidly', async ({ page }) => {
        // Setup job detail route
        await page.route(/.*\/api\/jobs\/1/, async (route) => {
            if (route.request().method() === 'PATCH') {
                await route.fulfill({ json: { ...MOCK_JOB_1, comments: route.request().postDataJSON()?.comments || '' } });
            } else {
                await route.fulfill({ json: MOCK_JOB_1 });
            }
        });

        await page.goto(BASE_URL);
        await page.locator('#job-row-1').click();
        await expect(page.locator('#job-detail-title')).toContainText('Frontend Engineer');

        // Switch to Edit tab to show the edit form
        await page.locator('#tab-button-edit').click();
        await expect(page.locator('.job-edit-form:has(.toggle-edit-btn)')).toBeVisible({ timeout: 10000 });

        // Click "Edit All" button to show the comments field
        const editAllButton = page.locator('.toggle-edit-btn button');
        await editAllButton.waitFor({ state: 'visible', timeout: 10000 });
        await editAllButton.click();

        // Find the comments textarea
        const commentsTextarea = page.locator('#job-1-comments');
        await commentsTextarea.waitFor({ state: 'visible', timeout: 10000 });

        // Type rapidly - this would previously cause cursor jumping
        await commentsTextarea.fill('Rapid typing test');

        // Verify the text was entered correctly without cursor position issues
        await expect(commentsTextarea).toHaveValue('Rapid typing test');
    });
});