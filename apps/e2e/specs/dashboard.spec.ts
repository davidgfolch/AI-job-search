import { test, expect } from './coverage.fixtures';
import { Page } from '@playwright/test';
import { BASE_URL, setupPageLogging, setupApiSafetyNet, setupAppBootstrapMocks } from './common.helpers';

test.use({
    bypassCSP: true,
});

async function setupDashboardMocks(page: Page) {
    await setupApiSafetyNet(page);
    await setupAppBootstrapMocks(page);
    await page.route(/.*\/api\/dashboard\/services/, async (route) => {
        await route.fulfill({
            contentType: 'application/json',
            json: {
                services: [
                    {
                        name: 'aienrich',
                        displayName: 'AI Enrich (Ollama)',
                        status: 'running',
                        usesOllama: true,
                        deployment: 'docker',
                        lastActivity: '2026-01-01T10:00:00',
                        metrics: { pendingJobs: 3, processed: 10, succeeded: 8, failed: 2, lastError: null, lastErrorAt: null },
                        recentErrors: [],
                    },
                    {
                        name: 'aicvmatcher',
                        displayName: 'CV Matcher',
                        status: 'stopped',
                        usesOllama: false,
                        deployment: 'host',
                        lastActivity: null,
                        metrics: { pendingJobs: 0, processed: 0, succeeded: 0, failed: 0, lastError: null, lastErrorAt: null },
                        recentErrors: [],
                    },
                ],
                ollama: {
                    reachable: true,
                    serverUrl: 'http://192.168.1.45:11434',
                    serverIp: '192.168.1.45',
                    isLan: true,
                    recentErrors: [],
                },
                prometheus: { reachable: true, url: 'http://host.docker.internal:9090' },
                grafana: { reachable: true, url: 'http://host.docker.internal:3000' },
                deployment: 'docker',
                timestamp: '2026-01-01T10:00:00Z',
            },
        });
    });
}

test.describe('Dashboard E2E', () => {
    test.beforeEach(async ({ page }) => {
        setupPageLogging(page);
        await setupDashboardMocks(page);
    });

    test('should show ollama reachable with its server ip and lan scope', async ({ page }) => {
        await page.goto(`${BASE_URL}/dashboard`);
        await expect(page.getByText('Connected')).toBeVisible();
        await expect(page.getByText('192.168.1.45')).toBeVisible();
        await expect(page.getByText('· LAN')).toBeVisible();
    });

    test('should show the deployment summary', async ({ page }) => {
        await page.goto(`${BASE_URL}/dashboard`);
        await expect(page.getByText('Deployment')).toBeVisible();
        await expect(page.locator('.summary-item').filter({ hasText: 'Deployment' })).toContainText('Docker');
    });

    test('should show prometheus and grafana health', async ({ page }) => {
        await page.goto(`${BASE_URL}/dashboard`);
        await expect(page.locator('.service-pill').filter({ hasText: 'Prometheus' })).toContainText('Up');
        await expect(page.locator('.service-pill').filter({ hasText: 'Grafana' })).toContainText('Up');
    });

    test('should show a docker/host tag on each service card', async ({ page }) => {
        await page.goto(`${BASE_URL}/dashboard`);
        const ollamaCard = page.locator('.service-card').filter({ hasText: 'AI Enrich (Ollama)' });
        await expect(ollamaCard).toBeVisible();
        await expect(ollamaCard.locator('.service-card-tag--deployment')).toContainText('Docker');
        const cvCard = page.locator('.service-card').filter({ hasText: 'CV Matcher' });
        await expect(cvCard).toBeVisible();
        await expect(cvCard.locator('.service-card-tag--deployment')).toContainText('Host');
    });

    test('should show services running grid', async ({ page }) => {
        await page.goto(`${BASE_URL}/dashboard`);
        await expect(page.locator('.summary-item').filter({ hasText: 'Services Running' })).toContainText('1/2');
        await expect(page.getByText('Services Running')).toBeVisible();
        await expect(page.getByText('Total Pending')).toBeVisible();
    });
});
