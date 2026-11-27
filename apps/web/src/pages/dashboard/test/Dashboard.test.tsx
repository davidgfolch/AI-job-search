import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Dashboard from '../Dashboard';
import type { DashboardData, InfrastructureService, ServiceStatus } from '../api/DashboardApi';

const mockUseDashboard = vi.hoisted(() => vi.fn());
vi.mock('../hooks/useDashboard', () => ({ useDashboard: () => mockUseDashboard(), REFRESH_INTERVAL_MS: 30000 }));

const service = (over: Partial<ServiceStatus> = {}): ServiceStatus => ({
    name: 'scrapper',
    displayName: 'Scrapper',
    status: 'running',
    lastActivity: null,
    usesOllama: false,
    deployment: 'docker',
    metrics: { pendingJobs: 3, processed: 1, succeeded: 1, failed: 0, lastError: null, lastErrorAt: null },
    recentErrors: [],
    ...over,
});

const infra = (name: string, over: Partial<InfrastructureService> = {}): InfrastructureService => ({
    name,
    displayName: name,
    kind: 'http',
    reachable: true,
    url: `http://${name}:1234`,
    detail: '/health',
    lastActivity: null,
    ...over,
});

const infrastructure: InfrastructureService[] = [
    infra('ollama', { kind: 'ollama', reachable: true, url: 'http://192.168.1.45:11434', serverIp: '192.168.1.45', isLan: true, detail: 'Ollama server' }),
    infra('backend'),
    infra('web'),
    infra('mysql', { kind: 'database', url: 'mysql://mysql_db:3306', detail: 'Connected' }),
    infra('mongo', { kind: 'database', url: 'mongodb://mongo_db:27017', detail: 'Connected' }),
    infra('aiformfiller'),
    infra('cron', { kind: 'activity', reachable: false, url: '/logs/cron/cron.jsonl', detail: 'No activity logged' }),
    infra('scrapper', { kind: 'activity', reachable: false, url: '/logs/scrapper/scrapper.jsonl', detail: 'No activity logged' }),
    infra('prometheus', { url: 'http://localhost:9090' }),
    infra('grafana', { url: 'http://localhost:3000' }),
];

const data: DashboardData = {
    services: [service(), service({ name: 'backend', displayName: 'Backend', status: 'stopped', deployment: 'host', metrics: { ...service().metrics, pendingJobs: 4 } })],
    infrastructure,
    ollama: { reachable: true, serverUrl: 'http://192.168.1.45:11434', serverIp: '192.168.1.45', isLan: true, recentErrors: [] },
    llmBackend: 'ollama',
    prometheus: { reachable: true, url: 'http://localhost:9090' },
    grafana: { reachable: true, url: 'http://localhost:3000' },
    deployment: 'docker',
    timestamp: '2026-01-01T00:00:00Z',
};

const withInfra = (name: string, over: Partial<InfrastructureService>): DashboardData => ({
    ...data,
    infrastructure: infrastructure.map(entry => entry.name === name ? { ...entry, ...over } : entry),
});

describe('Dashboard', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders the loading state only', () => {
        mockUseDashboard.mockReturnValue({ data: undefined, isLoading: true, isError: false });
        render(<Dashboard />);
        expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
        expect(screen.queryByText('Services Running')).not.toBeInTheDocument();
    });

    it.each([
        ['query error', { data: undefined, isLoading: false, isError: true }],
        ['missing data', { data: undefined, isLoading: false, isError: false }],
    ])('renders the failure state on %s', (_label, state) => {
        mockUseDashboard.mockReturnValue(state);
        render(<Dashboard />);
        expect(screen.getByText('Failed to load dashboard data')).toBeInTheDocument();
    });

    it('summarises running services, total pending jobs and ollama reachability', () => {
        mockUseDashboard.mockReturnValue({ data, isLoading: false, isError: false });
        render(<Dashboard />);
        expect(screen.getByRole('heading', { name: 'AI Job Search - Dashboard' })).toBeInTheDocument();
        expect(screen.getByText('1/2')).toBeInTheDocument();
        expect(screen.getByText('Services Running')).toBeInTheDocument();
        expect(screen.getByTestId('infra-ollama')).toHaveTextContent('Connected');
        expect(screen.getByText('7')).toBeInTheDocument();
        expect(screen.getByText('Total Pending')).toBeInTheDocument();
    });

    it('marks ollama as disconnected and styles it as an error', () => {
        mockUseDashboard.mockReturnValue({ data: withInfra('ollama', { reachable: false, detail: 'No Ollama server detected' }), isLoading: false, isError: false });
        render(<Dashboard />);
        expect(screen.getByText('Disconnected')).toBeInTheDocument();
        expect(screen.getByText('Disconnected')).toHaveClass('service-pill-value--error');
    });

    it('renders one card per service and the recent errors panel', () => {
        mockUseDashboard.mockReturnValue({ data, isLoading: false, isError: false });
        render(<Dashboard />);
        expect(document.querySelectorAll('.service-card')).toHaveLength(2);
        expect(screen.getByRole('heading', { name: 'Recent Errors' })).toBeInTheDocument();
        expect(screen.getByText('No recent errors found')).toBeInTheDocument();
    });

    it('shows the ollama server ip and lan scope', () => {
        mockUseDashboard.mockReturnValue({ data, isLoading: false, isError: false });
        render(<Dashboard />);
        expect(screen.getByText('192.168.1.45')).toBeInTheDocument();
        expect(screen.getByText('· LAN')).toBeInTheDocument();
    });

    it('shows prometheus and grafana with url', () => {
        mockUseDashboard.mockReturnValue({ data, isLoading: false, isError: false });
        render(<Dashboard />);
        expect(screen.getByText('http://localhost:9090')).toBeInTheDocument();
        expect(screen.getByText('http://localhost:3000')).toBeInTheDocument();
    });

    it('marks prometheus as down and styles it as an error', () => {
        mockUseDashboard.mockReturnValue({ data: withInfra('prometheus', { reachable: false }), isLoading: false, isError: false });
        render(<Dashboard />);
        expect(screen.getByText('Down')).toBeInTheDocument();
        expect(screen.getAllByText('Down')[0]).toHaveClass('service-pill-value--error');
    });

    it('renders every infrastructure service with its own status', () => {
        mockUseDashboard.mockReturnValue({ data, isLoading: false, isError: false });
        render(<Dashboard />);
        expect(screen.getByRole('heading', { name: 'Infrastructure' })).toBeInTheDocument();
        expect(document.querySelectorAll('.infra-card')).toHaveLength(10);
        expect(screen.getByTestId('infra-mysql')).toHaveTextContent('mysql://mysql_db:3306');
        expect(screen.getByTestId('infra-mysql')).toHaveTextContent('Connected');
        expect(screen.getByTestId('infra-cron')).toHaveTextContent('Idle');
    });

    it('reports database connection failures', () => {
        mockUseDashboard.mockReturnValue({ data: withInfra('mysql', { reachable: false, detail: 'pool exhausted' }), isLoading: false, isError: false });
        render(<Dashboard />);
        const mysql = screen.getByTestId('infra-mysql');
        expect(mysql).toHaveTextContent('pool exhausted');
        expect(mysql.querySelector('.service-pill-value')).toHaveClass('service-pill-value--error');
    });

    it('shows the last updated timestamp and autorefresh interval', () => {
        mockUseDashboard.mockReturnValue({ data, isLoading: false, isError: false });
        render(<Dashboard />);
        expect(screen.getByText('Last updated:')).toBeInTheDocument();
        expect(screen.getByText('Autorefresh every 30s')).toBeInTheDocument();
    });

    it('shows the deployment summary', () => {
        mockUseDashboard.mockReturnValue({ data, isLoading: false, isError: false });
        render(<Dashboard />);
        expect(screen.queryAllByText('Deployment').length).toBeGreaterThan(0);
        expect(screen.queryAllByText('Docker').length).toBeGreaterThan(0);
    });

    it('shows a docker/host tag on each service card', () => {
        mockUseDashboard.mockReturnValue({ data, isLoading: false, isError: false });
        render(<Dashboard />);
        expect(screen.queryAllByText('Host').length).toBeGreaterThan(0);
        expect(screen.queryAllByText('Docker').length).toBeGreaterThan(0);
    });
});
