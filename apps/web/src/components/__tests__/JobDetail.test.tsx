import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import JobDetail from '../JobDetail';
import type { Job, JobListParams } from '../../api/jobs';

const mockFilters: JobListParams = {
    page: 1,
    size: 20,
    search: 'test',
    order: 'created desc',
};

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
    interview_rh: false,
    interview: false,
    interview_tech: false,
    interview_technical_test: false,
    interview_technical_test_done: false,
    ai_enriched: true,
    easy_apply: false,
    required_technologies: 'React, TypeScript',
    optional_technologies: 'Python',
    client: 'Client A',
    comments: 'Initial comment',
    cv_match_percentage: 90,
};

const defaultProps = {
    job: mockJob,
    filters: mockFilters,
    onSeen: vi.fn(),
    onApplied: vi.fn(),
    onDiscarded: vi.fn(),
    onClosed: vi.fn(),
    onIgnore: vi.fn(),
    onNext: vi.fn(),
    onPrevious: vi.fn(),
    hasNext: true,
    hasPrevious: true,
};

describe('JobDetail', () => {
    it('renders job details correctly', () => {
        render(<JobDetail {...defaultProps} />);

        expect(screen.getByText('Software Engineer')).toBeInTheDocument();
        expect(screen.getByText('Tech Corp')).toBeInTheDocument();
        expect(screen.getByText('Job Description Content')).toBeInTheDocument();
        expect(screen.getByText('React, TypeScript')).toBeInTheDocument();
        expect(screen.getByText('Python')).toBeInTheDocument();
        expect(screen.getByText('100k')).toBeInTheDocument();
        expect(screen.getByText('Initial comment')).toBeInTheDocument();
    });

    it('renders job link correctly', () => {
        render(<JobDetail {...defaultProps} />);

        const link = screen.getByText('Software Engineer');
        expect(link).toHaveAttribute('href', 'http://example.com');
        expect(link).toHaveAttribute('target', '_blank');
    });

    it('displays CV match percentage when available', () => {
        render(<JobDetail {...defaultProps} />);

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
        render(<JobDetail {...defaultProps} job={jobWithoutOptionals} />);

        // These should not appear in the document
        expect(screen.queryByText('Company:')).not.toBeInTheDocument();
        expect(screen.queryByText('100k')).not.toBeInTheDocument();
        expect(screen.queryByText('Initial comment')).not.toBeInTheDocument();
    });

    it('renders permalink copy button', () => {
        render(<JobDetail {...defaultProps} />);

        const copyButton = screen.getByTitle('Copy permalink to clipboard');
        expect(copyButton).toBeInTheDocument();
        expect(copyButton).toHaveTextContent('🔗');
    });

    it('renders ignore button and calls onIgnore when clicked', () => {
        const onIgnore = vi.fn();
        render(<JobDetail {...defaultProps} onIgnore={onIgnore} />);

        const ignoreButton = screen.getByTitle('Mark as ignored');
        expect(ignoreButton).toBeInTheDocument();

        fireEvent.click(ignoreButton);
        expect(onIgnore).toHaveBeenCalledTimes(1);
    });

    it('renders seen button and calls onSeen when clicked', () => {
        const onSeen = vi.fn();
        render(<JobDetail {...defaultProps} onSeen={onSeen} />);

        const seenButton = screen.getByTitle('Mark as seen');
        expect(seenButton).toBeInTheDocument();

        fireEvent.click(seenButton);
        expect(onSeen).toHaveBeenCalledTimes(1);
    });

    it('renders applied button and calls onApplied when clicked', () => {
        const onApplied = vi.fn();
        render(<JobDetail {...defaultProps} onApplied={onApplied} />);

        const appliedButton = screen.getByTitle('Mark as applied');
        expect(appliedButton).toBeInTheDocument();

        fireEvent.click(appliedButton);
        expect(onApplied).toHaveBeenCalledTimes(1);
    });

    it('renders discarded button and calls onDiscarded when clicked', () => {
        const onDiscarded = vi.fn();
        render(<JobDetail {...defaultProps} onDiscarded={onDiscarded} />);

        const discardedButton = screen.getByTitle('Mark as discarded');
        expect(discardedButton).toBeInTheDocument();

        fireEvent.click(discardedButton);
        expect(onDiscarded).toHaveBeenCalledTimes(1);
    });

    it('renders closed button and calls onClosed when clicked', () => {
        const onClosed = vi.fn();
        render(<JobDetail {...defaultProps} onClosed={onClosed} />);

        const closedButton = screen.getByTitle('Mark as closed');
        expect(closedButton).toBeInTheDocument();

        fireEvent.click(closedButton);
        expect(onClosed).toHaveBeenCalledTimes(1);
    });

    it('renders navigation buttons', () => {
        render(<JobDetail {...defaultProps} />);

        const previousButton = screen.getByTitle('Previous job');
        const nextButton = screen.getByTitle('Next job');

        expect(previousButton).toBeInTheDocument();
        expect(nextButton).toBeInTheDocument();
    });

    it('calls onNext when Next button is clicked', () => {
        const onNext = vi.fn();
        render(<JobDetail {...defaultProps} onNext={onNext} />);

        const nextButton = screen.getByTitle('Next job');
        fireEvent.click(nextButton);

        expect(onNext).toHaveBeenCalledTimes(1);
    });

    it('calls onPrevious when Previous button is clicked', () => {
        const onPrevious = vi.fn();
        render(<JobDetail {...defaultProps} onPrevious={onPrevious} />);

        const previousButton = screen.getByTitle('Previous job');
        fireEvent.click(previousButton);

        expect(onPrevious).toHaveBeenCalledTimes(1);
    });

    it('disables Previous button when hasPrevious is false', () => {
        render(<JobDetail {...defaultProps} hasPrevious={false} />);

        const previousButton = screen.getByTitle('Previous job');
        expect(previousButton).toBeDisabled();
    });

    it('disables Next button when hasNext is false', () => {
        render(<JobDetail {...defaultProps} hasNext={false} />);

        const nextButton = screen.getByTitle('Next job');
        expect(nextButton).toBeDisabled();
    });
});
