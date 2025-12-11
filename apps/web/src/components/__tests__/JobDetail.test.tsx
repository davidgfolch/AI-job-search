import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import JobDetail from '../JobDetail';
import type { Job } from '../../api/jobs';
import { createMockJob } from '../../__tests__/test-utils';

const mockJob = createMockJob({
    markdown: 'Job Description Content',
    required_technologies: 'React, TypeScript',
    comments: 'Initial comment',
});

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

        const link = screen.getByText('Software Engineer');
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
            company: null,
            salary: null,
            comments: null,
            optional_technologies: null,
        };
        render(<JobDetail job={jobWithoutOptionals} />);

        // These should not appear in the document
        expect(screen.queryByText('Company:')).not.toBeInTheDocument();
        expect(screen.queryByText('100k')).not.toBeInTheDocument();
        expect(screen.queryByText('Initial comment')).not.toBeInTheDocument();
    });
});
