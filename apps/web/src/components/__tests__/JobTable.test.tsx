import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import JobTable from '../JobTable';
import { Job } from '../../api/jobs';

const mockJobs: Job[] = [
    {
        id: 1,
        title: 'Software Engineer',
        company: 'Tech Corp',
        salary: '100k',
        location: 'Remote',
        url: 'http://example.com',
        markdown: 'Description',
        web_page: 'LinkedIn',
        created: '2023-01-01',
        modified: null,
        flagged: false,
        like: false,
        ignored: false,
        seen: false,
        applied: false,
        discarded: false,
        closed: false,
        ai_enriched: true,
        required_technologies: 'React',
        optional_technologies: 'Python',
        client: null,
        comments: null,
        cv_match_percentage: 90,
    },
    {
        id: 2,
        title: 'Product Manager',
        company: 'Product Inc',
        salary: '120k',
        location: 'New York',
        url: 'http://example.com/2',
        markdown: 'Description 2',
        web_page: 'Indeed',
        created: '2023-01-02',
        modified: null,
        flagged: false,
        like: false,
        ignored: false,
        seen: false,
        applied: false,
        discarded: false,
        closed: false,
        ai_enriched: true,
        required_technologies: 'Agile',
        optional_technologies: 'Jira',
        client: null,
        comments: null,
        cv_match_percentage: 85,
    },
];

describe('JobTable', () => {
    it('renders job list correctly', () => {
        const onJobSelect = vi.fn();
        render(<JobTable jobs={mockJobs} selectedJob={null} onJobSelect={onJobSelect} />);

        expect(screen.getByText('Software Engineer')).toBeInTheDocument();
        expect(screen.getByText('Tech Corp')).toBeInTheDocument();
        expect(screen.getByText('100k')).toBeInTheDocument();

        expect(screen.getByText('Product Manager')).toBeInTheDocument();
        expect(screen.getByText('Product Inc')).toBeInTheDocument();
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

        fireEvent.click(screen.getByText('Software Engineer'));
        expect(onJobSelect).toHaveBeenCalledWith(mockJobs[0]);
    });
});
