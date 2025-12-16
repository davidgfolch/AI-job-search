import { render, screen } from '@testing-library/react';
import JobActions from '../JobActions';
import { describe, it, expect, vi } from 'vitest';
import type { Job } from '../../api/jobs';

const mockJob: Job = {
    id: 1,
    title: 'Test Job',
    company: 'Test Company',
    location: 'Test Location',
    salary: '100k',
    url: 'http://test.com',
    created: new Date().toISOString(),
    status: 'new',
    seen: false,
    applied: false,
    discarded: false,
    closed: false,
    ignored: false,
    flagged: false,
    like: false,
    ai_enriched: false,
};

const mockHandlers = {
    onSeen: vi.fn(),
    onApplied: vi.fn(),
    onDiscarded: vi.fn(),
    onClosed: vi.fn(),
    onIgnore: vi.fn(),
    onNext: vi.fn(),
    onPrevious: vi.fn(),
};

const mockFilters = {
    page: 1,
    size: 20,
    search: '',
    order: 'created desc',
};

describe('JobActions', () => {
    it('enables all buttons for single job selection', () => {
        render(
            <JobActions
                job={mockJob}
                filters={mockFilters}
                {...mockHandlers}
                hasNext={true}
                hasPrevious={true}
                isBulk={false}
            />
        );

        expect(screen.getByTitle('Mark as seen')).not.toBeDisabled();
        expect(screen.getByTitle('Mark as applied')).not.toBeDisabled();
        expect(screen.getByTitle('Mark as discarded')).not.toBeDisabled();
        expect(screen.getByTitle('Mark as closed')).not.toBeDisabled();
        expect(screen.getByTitle('Copy permalink to clipboard')).not.toBeDisabled();
        expect(screen.getByTitle('Previous job')).not.toBeDisabled();
        expect(screen.getByTitle('Next job')).not.toBeDisabled();
    });

    it('disables non-bulk actions even if job is present when isBulk is true', () => {
        render(
            <JobActions
                job={mockJob}
                filters={mockFilters}
                {...mockHandlers}
                hasNext={true}
                hasPrevious={true}
                isBulk={true}
            />
        );

        expect(screen.getByTitle('Mark as seen')).toBeDisabled();
        expect(screen.getByTitle('Mark as applied')).toBeDisabled();
        expect(screen.getByTitle('Mark as discarded')).toBeDisabled();
        expect(screen.getByTitle('Mark as closed')).toBeDisabled();
        // Ignore should be enabled
        expect(screen.getByTitle('Mark as ignored')).not.toBeDisabled();
        // Nav and Copy should be disabled
        expect(screen.getByTitle('Copy permalink to clipboard')).toBeDisabled();
        expect(screen.getByTitle('Previous job')).toBeDisabled();
        expect(screen.getByTitle('Next job')).toBeDisabled();
    });
});
