import { test, expect } from './coverage.fixtures';
import { Page } from '@playwright/test';
import { BASE_URL, setupPageLogging, setupAppBootstrapMocks } from './common.helpers';

test.use({
    bypassCSP: true,
});

async function setupDashboardMocks(page: Page) {
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
                infrastructure: [
                    { name: 'ollama', displayName: 'Ollama', kind: 'ollama', reachable: true, url: 'http://192.168.1.45:11434', detail: 'Ollama server', lastActivity: null, serverIp: '192.168.1.45', isLan: true },
                    { name: 'backend', displayName: 'Backend', kind: 'http', reachable: true, url: 'http://backend:8000', detail: '/health', lastActivity: null },
                    { name: 'web', displayName: 'Web', kind: 'http', reachable: true, url: 'http://web:5173', detail: '/', lastActivity: null },
                    { name: 'mysql', displayName: 'MySQL', kind: 'database', reachable: true, url: 'mysql://mysql_db:3306', detail: 'Connected', lastActivity: null },
                    { name: 'mongo', displayName: 'MongoDB', kind: 'database', reachable: true, url: 'mongodb://mongo_db:27017', detail: 'Connected', lastActivity: null },
                    { name: 'aiformfiller', displayName: 'AI Form Filler', kind: 'http', reachable: true, url: 'http://aiformfiller:8080', detail: '/api/health', lastActivity: null },
                    { name: 'cron', displayName: 'Cron', kind: 'activity', reachable: false, url: '/logs/cron/cron.jsonl', detail: 'No activity logged', lastActivity: null },
                    { name: 'scrapper', displayName: 'Scrapper', kind: 'activity', reachable: false, url: '/logs/scrapper/scrapper.jsonl', detail: 'No activity logged', lastActivity: null },
                    { name: 'prometheus', displayName: 'Prometheus', kind: 'http', reachable: true, url: 'http://host.docker.internal:9090', detail: '/-/healthy', lastActivity: null },
                    { name: 'grafana', displayName: 'Grafana', kind: 'http', reachable: true, url: 'http://host.docker.internal:3000', detail: '/api/health', lastActivity: null },
                ],
                ollama: {
                    reachable: true,
                    serverUrl: 'http://192.168.1.45:11434',
                    serverIp: '192.168.1.45',
                    isLan: true,
                    recentErrors: [],
                },
                llmBackend: 'ollama',
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
        const ollama = page.getByTestId('infra-ollama');
        await expect(ollama).toContainText('Connected');
        await expect(ollama).toContainText('192.168.1.45');
        await expect(ollama).toContainText('· LAN');
    });

    test('should show all infrastructure services', async ({ page }) => {
        await page.goto(`${BASE_URL}/dashboard`);
        await expect(page.locator('.infrastructure-grid')).toBeVisible();
        await expect(page.getByTestId('infra-mysql')).toContainText('mysql://mysql_db:3306');
        await expect(page.getByTestId('infra-mysql')).toContainText('Connected');
        await expect(page.getByTestId('infra-backend')).toContainText('Up');
        await expect(page.getByTestId('infra-mongo')).toContainText('mongodb://mongo_db:27017');
        await expect(page.getByTestId('infra-aiformfiller')).toContainText('Up');
        await expect(page.getByTestId('infra-cron')).toContainText('Idle');
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

    test('should show the configured LLM backend pill', async ({ page }) => {
        await page.goto(`${BASE_URL}/dashboard`);
        await expect(page.locator('.service-pill').filter({ hasText: 'LLM Backend' })).toContainText('ollama');
    });

    test('should show services running grid', async ({ page }) => {
        await page.goto(`${BASE_URL}/dashboard`);
        await expect(page.locator('.summary-item').filter({ hasText: 'Services Running' })).toContainText('1/2');
        await expect(page.getByText('Services Running')).toBeVisible();
        await expect(page.getByText('Total Pending')).toBeVisible();
    });
});
