import { render, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import Viewer from '../Viewer';
import type { Job } from '../../api/jobs';
import React from 'react';

// --- Constants ---
export const mockJobs: Job[] = [
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

// --- Helpers ---
export const renderViewer = (initialEntries = ['/']) => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return render(
        <MemoryRouter initialEntries={initialEntries}>
            <QueryClientProvider client={client}><Viewer /></QueryClientProvider>
        </MemoryRouter>
    );
};

export const waitForAsync = async () => await act(async () => { await new Promise(r => setTimeout(r, 0)); });
