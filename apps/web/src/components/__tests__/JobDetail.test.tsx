import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
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
        render(<JobDetail job={mockJob} />);

        expect(screen.getByText('Software Engineer')).toBeInTheDocument();
        expect(screen.getByText('Tech Corp')).toBeInTheDocument();
        expect(screen.getByText('Job Description Content')).toBeInTheDocument();
        expect(screen.getByText('React, TypeScript')).toBeInTheDocument();
        expect(screen.getByText('Python')).toBeInTheDocument();
        expect(screen.getByText('100k')).toBeInTheDocument();
        expect(screen.getByText('Initial comment')).toBeInTheDocument();
    });

    it('renders job link correctly', () => {
        render(<JobDetail job={mockJob} />);

        const link = screen.getByText('View Job →');
        expect(link).toHaveAttribute('href', 'http://example.com');
        expect(link).toHaveAttribute('target', '_blank');
    });

    it('displays CV match percentage when available', () => {
        render(<JobDetail job={mockJob} />);

        expect(screen.getByText('90%')).toBeInTheDocument();
    });

    it('does not display optional fields when they are null', () => {
        const jobWithoutOptionals: Job = {
            ...mockJob,
            company: '',
            salary: '',
            comments: '',
            optional_technologies: '',
        };
        render(<JobDetail job={jobWithoutOptionals} />);

        // These should not appear in the document
        expect(screen.queryByText('Company:')).not.toBeInTheDocument();
        expect(screen.queryByText('100k')).not.toBeInTheDocument();
        expect(screen.queryByText('Initial comment')).not.toBeInTheDocument();
    });
});
