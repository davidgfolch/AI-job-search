import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import JobTable from '../JobTable';
import { createMockJobs } from '../../__tests__/test-utils';

const mockJobs = createMockJobs(2, {
    required_technologies: 'React',
    optional_technologies: 'Python',
});

describe('JobTable', () => {
    it('renders job list correctly', () => {
        const onJobSelect = vi.fn();
        render(<JobTable jobs={mockJobs} selectedJob={null} onJobSelect={onJobSelect} />);

        expect(screen.getByText('Job 1')).toBeInTheDocument();
        expect(screen.getByText('Company 1')).toBeInTheDocument();
        expect(screen.getByText('100k')).toBeInTheDocument();

        expect(screen.getByText('Job 2')).toBeInTheDocument();
        expect(screen.getByText('Company 2')).toBeInTheDocument();
        expect(screen.getByText('120k')).toBeInTheDocument();
    });

    it('highlights selected job', () => {
        const onJobSelect = vi.fn();
        render(<JobTable jobs={mockJobs} selectedJob={mockJobs[0]} onJobSelect={onJobSelect} />);

        const rows = screen.getAllByRole('row');
        // Header + 2 data rows. First data row should be selected.
        expect(rows[1]).toHaveClass('selected');
        expect(rows[2]).not.toHaveClass('selected');
    });

    it('calls onJobSelect when a row is clicked', () => {
        const onJobSelect = vi.fn();
        render(<JobTable jobs={mockJobs} selectedJob={null} onJobSelect={onJobSelect} />);

        fireEvent.click(screen.getByText('Job 1'));
        expect(onJobSelect).toHaveBeenCalledWith(mockJobs[0]);
    });
});
