import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Viewer from '../Viewer';
import { jobsApi } from '../../api/jobs';
import type { Job } from '../../api/jobs';

// --- Mocks ---
globalThis.IntersectionObserver = vi.fn(function (this: any) {
    this.observe = vi.fn();
    this.unobserve = vi.fn();
    this.disconnect = vi.fn();
}) as any;

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

// --- Constants & Helpers ---
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

const renderViewer = (initialEntries = ['/']) => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return render(
        <MemoryRouter initialEntries={initialEntries}>
            <QueryClientProvider client={client}><Viewer /></QueryClientProvider>
        </MemoryRouter>
    );
};

const waitForAsync = async () => await act(async () => { await new Promise(r => setTimeout(r, 0)); });

// --- Tests ---
describe('Viewer', () => {
    beforeEach(() => { vi.clearAllMocks(); });

    const stateTestCases = [
        {
            name: 'renders loading state initially',
            mockSetup: () => (jobsApi.getJobs as any).mockReturnValue(new Promise(() => { })),
            assertion: async () => {
                expect(screen.getByText('Loading jobs...')).toBeInTheDocument();
                await waitForAsync();
            }
        },
        {
            name: 'renders job list after loading',
            mockSetup: () => (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 }),
            assertion: async () => {
                await waitFor(() => {
                    expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
                    expect(screen.getAllByText('Job 2').length).toBeGreaterThan(0);
                });
                const summary = screen.getByText(/ loaded \| /);
                expect(summary).toHaveTextContent(/2\/2 loaded \| 0 Selected/);
            }
        },
        {
            name: 'handles error state',
            mockSetup: () => (jobsApi.getJobs as any).mockRejectedValue(new Error('Failed to fetch')),
            assertion: async () => await waitFor(() => expect(screen.getByText('Failed to fetch')).toBeInTheDocument())
        }
    ];

    it.each(stateTestCases)('$name', async ({ mockSetup, assertion }) => {
        mockSetup();
        renderViewer();
        await assertion();
    });

    it('handles user interactions: select, verify details, partial filter', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
        renderViewer();
        await waitFor(() => expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0));

        // Interaction: Select Job
        expect(screen.getByText('Select a job to view details')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('cell', { name: 'Job 1' }));
        expect(screen.getByText('Description 1')).toBeInTheDocument();
        expect(screen.getAllByText('Company 1')).toHaveLength(2);

        // Interaction: Filter (Flagged)
        const flaggedButtons = screen.getAllByRole('button', { name: /Flagged/i });
        fireEvent.click(flaggedButtons[0]);
        await waitFor(() => expect(jobsApi.getJobs).toHaveBeenCalledWith(expect.objectContaining({ flagged: true, page: 1 })));
        
        await waitForAsync();
    });

    it('handles tab switching and edit interactions', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
        (jobsApi.getJob as any).mockResolvedValue(mockJobs[0]);
        renderViewer();
        await waitFor(() => expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0));

        // Select and Switch to Edit
        fireEvent.click(screen.getByRole('cell', { name: 'Job 1' }));
        fireEvent.click(screen.getByText('Edit'));
        expect(screen.getByLabelText('Comments')).toBeInTheDocument();

        // Switch back to List
        fireEvent.click(screen.getByText('List'));
        expect(screen.getByRole('cell', { name: 'Job 1' })).toBeInTheDocument();
        
        await waitForAsync();
    });

    it('handles infinite scroll', async () => {
         // Infinite Scroll
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 50, page: 1, size: 20 });
        renderViewer();
        await waitFor(() => {
            const summary = screen.getByText(/ loaded \| /);
            expect(summary).toHaveTextContent(/2\/50 loaded \| 0 Selected/);
        });
        expect(jobsApi.getJobs).toHaveBeenCalledTimes(1);
    });

    it('updates job and refreshes list (isolated)', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
        (jobsApi.getJob as any).mockResolvedValue(mockJobs[0]);
        (jobsApi.updateJob as any).mockResolvedValue({ ...mockJobs[0], flagged: true });
        renderViewer();
        
        await waitFor(() => expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0));
        fireEvent.click(screen.getByRole('cell', { name: 'Job 1' }));
        fireEvent.click(screen.getByText('Edit'));

        const flaggedPills = screen.getAllByText('Flagged');
        fireEvent.click(flaggedPills[flaggedPills.length - 1]);
        await waitFor(() => expect(jobsApi.updateJob).toHaveBeenCalledWith(1, { flagged: true }));
        expect(jobsApi.getJobs).toHaveBeenCalledTimes(2);
        await waitForAsync();
    });

    it('filters by URL ids', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
        renderViewer(['/?ids=1,2']);
        await waitFor(() => expect(jobsApi.getJobs).toHaveBeenCalledWith(expect.objectContaining({ sql_filter: 'id IN (1,2)', page: 1 })));
    });

    it('validates configuration name on save', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
        renderViewer();
        await waitFor(() => expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0));

        fireEvent.click(screen.getByText(/Filters/));
        fireEvent.click(screen.getByText('Save'));
        await waitFor(() => expect(screen.getByText('Please enter a name for the configuration')).toBeInTheDocument());
        
        fireEvent.click(screen.getByText('Please enter a name for the configuration'));
        await waitFor(() => expect(screen.queryByText('Please enter a name for the configuration')).not.toBeInTheDocument());
    });
});
