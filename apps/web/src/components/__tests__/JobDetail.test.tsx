import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import JobDetail from '../JobDetail';
import { Job } from '../../api/jobs';

const mockJob: Job = {
    id: 1,
    title: 'Software Engineer',
    company: 'Tech Corp',
    salary: '100k',
    location: 'Remote',
    url: 'http://example.com',
    markdown: 'Job Description Content',
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
    required_technologies: 'React, TypeScript',
    optional_technologies: 'Python',
    client: 'Client A',
    comments: 'Initial comment',
    cv_match_percentage: 90,
};

describe('JobDetail', () => {
    it('renders job details correctly', () => {
        const onUpdate = vi.fn();
        render(<JobDetail job={mockJob} onUpdate={onUpdate} />);

        expect(screen.getByText('Software Engineer')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Tech Corp')).toBeInTheDocument();
        expect(screen.getByText('Job Description Content')).toBeInTheDocument();
        expect(screen.getByText('React, TypeScript')).toBeInTheDocument();
    });

    it('calls onUpdate when status is toggled', () => {
        const onUpdate = vi.fn();
        render(<JobDetail job={mockJob} onUpdate={onUpdate} />);

        const appliedButton = screen.getByText('applied');
        fireEvent.click(appliedButton);

        expect(onUpdate).toHaveBeenCalledWith({ applied: true });
    });

    it('updates local state and calls onUpdate on save', () => {
        const onUpdate = vi.fn();
        render(<JobDetail job={mockJob} onUpdate={onUpdate} />);

        const commentsInput = screen.getByLabelText('Comments');
        fireEvent.change(commentsInput, { target: { value: 'New comment' } });

        const saveButton = screen.getByText('Save Changes');
        fireEvent.click(saveButton);

        expect(onUpdate).toHaveBeenCalledWith({
            comments: 'New comment',
            salary: '100k',
            company: 'Tech Corp',
            client: 'Client A',
        });
    });
});
