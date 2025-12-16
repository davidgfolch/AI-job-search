import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Viewer from '../Viewer';
import { jobsApi } from '../../api/jobs';
import type { Job } from '../../api/jobs';

// Mock IntersectionObserver
globalThis.IntersectionObserver = vi.fn(function (this: any) {
    this.observe = vi.fn();
    this.unobserve = vi.fn();
    this.disconnect = vi.fn();
}) as any;

// Mock the jobs API
vi.mock('../../api/jobs', async () => {
    const actual = await vi.importActual('../../api/jobs');
    return {
        ...actual,
        jobsApi: {
            getJobs: vi.fn(),
            getJob: vi.fn(),
            updateJob: vi.fn(),
            getAppliedJobsByCompany: vi.fn().mockResolvedValue([]),
        },
    };
});

const mockJobs: Job[] = [
    {
        id: 1, title: 'Job 1', company: 'Company 1', salary: '100k', location: 'Remote', url: 'http://example.com/1', markdown: 'Description 1',
        web_page: 'LinkedIn', created: '2023-01-01', modified: null, flagged: false, like: false, ignored: false, seen: false, applied: false,
        discarded: false, closed: false, interview_rh: false, interview: false, interview_tech: false, interview_technical_test: false,
        interview_technical_test_done: false, ai_enriched: true, easy_apply: false, required_technologies: 'React', optional_technologies: null,
        client: null, comments: null, cv_match_percentage: 90,
    },
    {
        id: 2, title: 'Job 2', company: 'Company 2', salary: '120k', location: 'Remote', url: 'http://example.com/2', markdown: 'Description 2',
        web_page: 'Indeed', created: '2023-01-02', modified: null, flagged: true, like: false, ignored: false, seen: true, applied: false,
        discarded: false, closed: false, interview_rh: false, interview: false, interview_tech: false, interview_technical_test: false,
        interview_technical_test_done: false, ai_enriched: false, easy_apply: true, required_technologies: 'Python', optional_technologies: null,
        client: null, comments: null, cv_match_percentage: 80,
    },
];

const createTestQueryClient = () => new QueryClient({
    defaultOptions: { queries: { retry: false, }, },
});

const renderWithRouter = (ui: React.ReactElement, { initialEntries = ['/'] }: { initialEntries?: string[] } = {}) => {
    return render(
        <MemoryRouter initialEntries={initialEntries}>
            <QueryClientProvider client={createTestQueryClient()}>
                {ui}
            </QueryClientProvider>
        </MemoryRouter>
    );
};

const waitForAsync = async () => {
    await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
    });
};

describe('Viewer', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders loading state initially', async () => {
        (jobsApi.getJobs as any).mockReturnValue(new Promise(() => { })); // Never resolves
        renderWithRouter(<Viewer />);
        expect(screen.getByText('Loading jobs...')).toBeInTheDocument();
        await waitForAsync();
    });

    it('renders job list after loading', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20, });
        renderWithRouter(<Viewer />);
        await waitFor(() => {
            // Use getAllByText because "Job 1" might appear in multiple places if we are not careful,
            // but here we just want to ensure it is present.
            expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
            expect(screen.getAllByText('Job 2').length).toBeGreaterThan(0);
        });
        const summary = screen.getByText(/ loaded \| /);
        expect(summary).toHaveTextContent(/2\/2 loaded \| 0 Selected/);
    });

    it('handles error state', async () => {
        (jobsApi.getJobs as any).mockRejectedValue(new Error('Failed to fetch'));
        renderWithRouter(<Viewer />);
        await waitFor(() => {
            expect(screen.getByText('Failed to fetch')).toBeInTheDocument();
        });
    });

    it('selects a job and displays details', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20, });
        renderWithRouter(<Viewer />);
        await waitFor(() => {
            expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
        });
        // Initially no selection
        expect(screen.getByText('Select a job to view details')).toBeInTheDocument();
        // Click first job in the list (use role cell to be specific to the table)
        // Note: JobTable renders title in a cell
        const jobLink = screen.getByRole('cell', { name: 'Job 1' });
        fireEvent.click(jobLink);
        // Should show details
        expect(screen.getByText('Description 1')).toBeInTheDocument();
        // Company 1 appears in list and detail, so we expect 2
        expect(screen.getAllByText('Company 1')).toHaveLength(2);
        
        await waitForAsync();
    });

    it('switches between List and Edit tabs', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20, });
        (jobsApi.getJob as any).mockResolvedValue(mockJobs[0]);
        renderWithRouter(<Viewer />);
        await waitFor(() => {
            expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
        });
        // Select a job first
        const jobLink = screen.getByRole('cell', { name: 'Job 1' });
        fireEvent.click(jobLink);
        // Switch to Edit tab
        fireEvent.click(screen.getByText('Edit'));
        // Should show edit form
        expect(screen.getByLabelText('Comments')).toBeInTheDocument();
        // Switch back to List tab
        fireEvent.click(screen.getByText('List'));
        // Should show list again (check for table cell)
        expect(screen.getByRole('cell', { name: 'Job 1' })).toBeInTheDocument();
        
        await waitForAsync();
    });

    it('handles infinite scroll loading', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 50, page: 1, size: 20, });
        renderWithRouter(<Viewer />);
        await waitFor(() => {
            const summary = screen.getByText(/ loaded \| /);
            expect(summary).toHaveTextContent(/2\/50 loaded \| 0 Selected/);
        });
        // Initially showing 2 jobs from page 1
        expect(jobsApi.getJobs).toHaveBeenCalledTimes(1);
    });

    it('updates job and refreshes list', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20, });
        (jobsApi.getJob as any).mockResolvedValue(mockJobs[0]);
        (jobsApi.updateJob as any).mockResolvedValue({
            ...mockJobs[0],
            flagged: true,
        });
        renderWithRouter(<Viewer />);
        await waitFor(() => {
            expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
        });
        // Select job
        const jobLink = screen.getByRole('cell', { name: 'Job 1' });
        fireEvent.click(jobLink);
        // Go to edit tab
        fireEvent.click(screen.getByText('Edit'));
        // Click flagged pill in the edit form (appears multiple times due to filters)
        const flaggedPills = screen.getAllByText('Flagged');
        // The last ones are in the Edit form's status pills
        const flaggedPill = flaggedPills[flaggedPills.length - 1];
        fireEvent.click(flaggedPill);
        await waitFor(() => {
            expect(jobsApi.updateJob).toHaveBeenCalledWith(1, { flagged: true });
        });
        // Should invalidate queries (refetch jobs)
        expect(jobsApi.getJobs).toHaveBeenCalledTimes(2); // Initial + Refetch
        
        await waitForAsync();
    });
    it('filters jobs by ids from URL', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20, });
        renderWithRouter(<Viewer />, { initialEntries: ['/?ids=1,2'] });
        await waitFor(() => {
            expect(jobsApi.getJobs).toHaveBeenCalledWith(expect.objectContaining({
                sql_filter: 'id IN (1,2)',
                page: 1,
            }));
        });
    });
    it('interactions with filters trigger API calls', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
        renderWithRouter(<Viewer />);
        
        await waitFor(() => {
            expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
        });

        // Toggle a filter explicitly (e.g. "Flagged")
        // We have two "Flagged" buttons (Include and Exclude). 
        // We want to click the one in "Include" section.
        // We can find all buttons with text "Flagged" and click the first one.
        const flaggedButtons = screen.getAllByRole('button', { name: /Flagged/i });
        fireEvent.click(flaggedButtons[0]);

        await waitFor(() => {
            expect(jobsApi.getJobs).toHaveBeenCalledWith(expect.objectContaining({
                flagged: true,
                page: 1
            }));
        });
    });

    it('dismisses message when close button is clicked', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
        renderWithRouter(<Viewer />);
        
        await waitFor(() => {
            expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
        });

        // Toggle filters to show configurations
        const toggleBtn = screen.getByText(/Filters/);
        fireEvent.click(toggleBtn);

        // Find Save button in FilterConfigurations and click it empty
        const saveBtn = screen.getByText('Save');
        fireEvent.click(saveBtn);

        // Should show error message from validation
        await waitFor(() => {
            expect(screen.getByText('Please enter a name for the configuration')).toBeInTheDocument();
        });

        // Dismiss it
        const messageEl = screen.getByText('Please enter a name for the configuration');
        fireEvent.click(messageEl);

        await waitFor(() => {
            expect(screen.queryByText('Please enter a name for the configuration')).not.toBeInTheDocument();
        });
    });
});
