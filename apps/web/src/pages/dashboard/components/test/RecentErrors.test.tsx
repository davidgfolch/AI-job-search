import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import RecentErrors from '../RecentErrors';
import type { ServiceStatus } from '../../api/DashboardApi';

const serviceWithErrors = (displayName: string, recentErrors: ServiceStatus['recentErrors']): ServiceStatus => ({
    name: displayName.toLowerCase(),
    displayName,
    status: 'error',
    lastActivity: null,
    usesOllama: false,
    metrics: { pendingJobs: 0, processed: 0, succeeded: 0, failed: 0, lastError: null, lastErrorAt: null },
    recentErrors,
});

const error = (over: Partial<ServiceStatus['recentErrors'][number]> = {}) => ({ timestamp: '2026-01-01T10:00:00Z', event: 'sync.failed', level: 'error', message: 'boom', ...over });

describe('RecentErrors', () => {
    it('shows the empty message when no service reports errors', () => {
        render(<RecentErrors services={[serviceWithErrors('Scrapper', [])]} />);
        expect(screen.getByRole('heading', { name: 'Recent Errors' })).toBeInTheDocument();
        expect(screen.getByText('No recent errors found')).toBeInTheDocument();
    });

    it('shows the empty message for an empty service list', () => {
        render(<RecentErrors services={[]} />);
        expect(screen.getByText('No recent errors found')).toBeInTheDocument();
    });

    it('collects errors from every service, tags the owning service and sorts newest first', () => {
        render(
            <RecentErrors
                services={[
                    serviceWithErrors('Scrapper', [error({ message: 'older', timestamp: '2026-01-01T09:00:00Z' })]),
                    serviceWithErrors('Backend', [error({ message: 'newest', timestamp: '2026-01-01T11:00:00Z' })]),
                ]}
            />
        );
        expect(screen.getByRole('heading', { name: 'Recent Errors (2)' })).toBeInTheDocument();
        const messages = screen.getAllByText(/older|newest/);
        expect(messages.map(node => node.textContent)).toEqual(['newest', 'older']);
        expect(screen.getByText('Backend')).toBeInTheDocument();
        expect(screen.getByText('Scrapper')).toBeInTheDocument();
    });

    it('applies the level as a css class and exposes the message as a tooltip', () => {
        render(<RecentErrors services={[serviceWithErrors('Scrapper', [error({ level: 'warning' })])]} />);
        expect(screen.getByText('boom')).toHaveAttribute('title', 'boom');
        expect(screen.getByText('boom').closest('.error-entry')).toHaveClass('error-entry--warning');
    });

    it('renders an empty timestamp when the error has none', () => {
        render(<RecentErrors services={[serviceWithErrors('Scrapper', [error({ timestamp: '' })])]} />);
        expect(screen.getAllByText('sync.failed')).toHaveLength(1);
    });

    it('caps the list at 15 entries', () => {
        const many = Array.from({ length: 20 }, (_, i) => error({ message: `err-${i}`, timestamp: `2026-01-01T10:${String(i).padStart(2, '0')}:00Z` }));
        render(<RecentErrors services={[serviceWithErrors('Scrapper', many)]} />);
        expect(screen.getByRole('heading', { name: 'Recent Errors (15)' })).toBeInTheDocument();
        expect(screen.getByText('err-19')).toBeInTheDocument();
        expect(screen.queryByText('err-04')).not.toBeInTheDocument();
    });
});