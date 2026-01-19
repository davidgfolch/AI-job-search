import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import JobTable from '../JobTable';
import { createMockJobs } from '../../__tests__/test-utils';

const mockJobs = createMockJobs(2, {
    required_technologies: 'React',
    optional_technologies: 'Python',
});

describe('JobTable', () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    const defaultProps = {
        jobs: mockJobs,
        selectedJob: null,
        onJobSelect: vi.fn(),
        selectedIds: new Set<number>(),
        selectionMode: 'none' as const,
        onToggleSelectJob: vi.fn(),
        onToggleSelectAll: vi.fn(),
    };

    it('renders job list correctly', () => {
        render(<JobTable {...defaultProps} />);

        expect(screen.getByText('Job 1')).toBeInTheDocument();
        expect(screen.getByText('Company 1')).toBeInTheDocument();
        expect(screen.getByText('100k')).toBeInTheDocument();
        expect(screen.getByText('Created')).toBeInTheDocument();
        // Since mock jobs might not have created date set or it's old, let's just check if the column exists effectively
        // We'll check for '-' if date is missing or specific value if we set it.
        // The createMockJobs utility might not set 'created' by default to a fresh date.
        
        expect(screen.getByText('Job 2')).toBeInTheDocument();
        expect(screen.getByText('Company 2')).toBeInTheDocument();
        expect(screen.getByText('120k')).toBeInTheDocument();
    });

    it('displays lapsed time correctly with tooltip', () => {
        const now = new Date('2023-10-15T12:00:00Z');
        vi.setSystemTime(now);
        
        const jobsWithDate = [
            { ...mockJobs[0], created: '2023-10-10T12:00:00Z' }, // 5 days ago
        ];
        render(<JobTable {...defaultProps} jobs={jobsWithDate} />);
        
        const cell = screen.getByText('5d ago');
        expect(cell).toBeInTheDocument();
        expect(cell).toHaveAttribute('title', '5 days ago');
    });

    it('highlights selected job', () => {
        render(<JobTable {...defaultProps} selectedJob={mockJobs[0]} />);

        const rows = screen.getAllByRole('row');
        // Header + 2 data rows. First data row should be selected.
        expect(rows[1]).toHaveClass('selected');
        expect(rows[2]).not.toHaveClass('selected');
    });

    it('calls onJobSelect when a row is clicked', () => {
        const onJobSelect = vi.fn();
        render(<JobTable {...defaultProps} onJobSelect={onJobSelect} />);

        fireEvent.click(screen.getByText('Job 1'));
        expect(onJobSelect).toHaveBeenCalledWith(mockJobs[0]);
    });
});
