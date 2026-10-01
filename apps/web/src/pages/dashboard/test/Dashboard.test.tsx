import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Dashboard from '../Dashboard';
import type { DashboardData, ServiceStatus } from '../api/DashboardApi';

const mockUseDashboard = vi.hoisted(() => vi.fn());
vi.mock('../hooks/useDashboard', () => ({ useDashboard: () => mockUseDashboard() }));

const service = (over: Partial<ServiceStatus> = {}): ServiceStatus => ({
    name: 'scrapper',
    displayName: 'Scrapper',
    status: 'running',
    lastActivity: null,
    usesOllama: false,
    metrics: { pendingJobs: 3, processed: 1, succeeded: 1, failed: 0, lastError: null, lastErrorAt: null },
    recentErrors: [],
    ...over,
});

const data: DashboardData = {
    services: [service(), service({ name: 'backend', displayName: 'Backend', status: 'stopped', metrics: { ...service().metrics, pendingJobs: 4 } })],
    ollama: { reachable: true, recentErrors: [] },
    timestamp: '2026-01-01T00:00:00Z',
};

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
        expect(screen.getByText('Connected')).toBeInTheDocument();
        expect(screen.getByText('7')).toBeInTheDocument();
        expect(screen.getByText('Total Pending')).toBeInTheDocument();
    });

    it('marks ollama as disconnected and styles it as an error', () => {
        mockUseDashboard.mockReturnValue({ data: { ...data, ollama: { reachable: false, recentErrors: [] } }, isLoading: false, isError: false });
        render(<Dashboard />);
        expect(screen.getByText('Disconnected')).toBeInTheDocument();
        expect(screen.getByText('Disconnected')).toHaveClass('summary-value--error');
    });

    it('renders one card per service and the recent errors panel', () => {
        mockUseDashboard.mockReturnValue({ data, isLoading: false, isError: false });
        render(<Dashboard />);
        expect(screen.getByText('Scrapper')).toBeInTheDocument();
        expect(screen.getByText('Backend')).toBeInTheDocument();
        expect(screen.getByRole('heading', { name: 'Recent Errors' })).toBeInTheDocument();
        expect(screen.getByText('No recent errors found')).toBeInTheDocument();
    });
});