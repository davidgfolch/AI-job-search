import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import JobActions from '../JobActions';
import type { Job } from '../../api/jobs';

describe('JobActions', () => {
    const mockJob: Job = {
        id: 1,
        title: 'Test Job',
        company: 'Test Company',
        location: 'Remote',
        salary: null,
        url: 'http://example.com',
        markdown: null,
        web_page: null,
        created: null,
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
        ai_enriched: false,
        easy_apply: false,
        required_technologies: null,
        optional_technologies: null,
        client: null,
        comments: null,
        cv_match_percentage: null
    };

    const defaultProps = {
        job: mockJob,
        filters: {},
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

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders all action buttons', () => {
        render(<JobActions {...defaultProps} />);
        
        expect(screen.getByTitle('Mark as seen')).toBeInTheDocument();
        expect(screen.getByTitle('Mark as applied')).toBeInTheDocument();
        expect(screen.getByTitle('Mark as discarded')).toBeInTheDocument();
        expect(screen.getByTitle('Mark as closed')).toBeInTheDocument();
        expect(screen.getByTitle('Mark as ignored')).toBeInTheDocument();
        expect(screen.getByTitle('Copy permalink to clipboard')).toBeInTheDocument();
        expect(screen.getByTitle('Previous job')).toBeInTheDocument();
        expect(screen.getByTitle('Next job')).toBeInTheDocument();
    });

    it('calls callback functions when buttons are clicked', () => {
        render(<JobActions {...defaultProps} />);

        fireEvent.click(screen.getByTitle('Mark as seen'));
        expect(defaultProps.onSeen).toHaveBeenCalled();

        fireEvent.click(screen.getByTitle('Mark as applied'));
        expect(defaultProps.onApplied).toHaveBeenCalled();

        fireEvent.click(screen.getByTitle('Mark as discarded'));
        expect(defaultProps.onDiscarded).toHaveBeenCalled();

        fireEvent.click(screen.getByTitle('Mark as closed'));
        expect(defaultProps.onClosed).toHaveBeenCalled();

        fireEvent.click(screen.getByTitle('Mark as ignored'));
        expect(defaultProps.onIgnore).toHaveBeenCalled();
    });

    it('calls navigation callbacks', () => {
        render(<JobActions {...defaultProps} />);

        fireEvent.click(screen.getByTitle('Next job'));
        expect(defaultProps.onNext).toHaveBeenCalled();

        fireEvent.click(screen.getByTitle('Previous job'));
        expect(defaultProps.onPrevious).toHaveBeenCalled();
    });

    it('disables navigation buttons correctly', () => {
        render(<JobActions {...defaultProps} hasNext={false} hasPrevious={false} />);

        expect(screen.getByTitle('Next job')).toBeDisabled();
        expect(screen.getByTitle('Previous job')).toBeDisabled();
    });

    it('copies permalink to clipboard', async () => {
        const writeTextMock = vi.fn();
        Object.assign(navigator, {
            clipboard: {
                writeText: writeTextMock,
            },
        });

        // Mock window.location
        Object.defineProperty(window, 'location', {
            value: {
                origin: 'http://localhost',
                pathname: '/test',
            },
            writable: true,
        });

        const filters = { search: 'react', flagged: true };
        render(<JobActions {...defaultProps} filters={filters} />);

        fireEvent.click(screen.getByTitle('Copy permalink to clipboard'));

        expect(writeTextMock).toHaveBeenCalledWith(expect.stringContaining('http://localhost/test?'));
        expect(writeTextMock).toHaveBeenCalledWith(expect.stringContaining('jobId=1'));
        expect(writeTextMock).toHaveBeenCalledWith(expect.stringContaining('search=react'));
        expect(writeTextMock).toHaveBeenCalledWith(expect.stringContaining('flagged=true'));
    });
});
