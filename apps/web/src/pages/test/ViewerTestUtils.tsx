import { render, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import Viewer from "../viewer/Viewer";
import type { Job } from '../viewer/api/ViewerApi';
import React from 'react';

// --- Constants ---
export const mockJobs: Job[] = [
    {
        id: 1, title: 'Job 1', company: 'Company 1', salary: '100k', location: 'Remote', url: 'http://example.com/1', markdown: 'Description 1',
        web_page: 'LinkedIn', created: '2023-01-01', modified: null, flagged: false, like: false, ignored: false, seen: false, applied: false,
        discarded: false, closed: false, interview_rh: false, interview: false, interview_tech: false, interview_technical_test: false,
        interview_technical_test_done: false,    ai_enriched: false,
    easy_apply: false,
    required_technologies: "React, TypeScript",
    optional_technologies: "Node.js",
    client: "Client A",
    comments: "Test comment",
    cv_match_percentage: 85,
    ai_enrich_error: null,
  },
  {
    id: 2,
    title: "Job 2",
    company: "Company 2",
    location: "Remote",
    salary: "120k",
    url: "http://example.com/2",
    markdown: "Description 2",
    web_page: "http://example.com/2",
    created: "2023-01-02",
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
    required_technologies: "Vue, JavaScript",
    optional_technologies: "Python",
    client: "Client B",
    comments: "Another comment",
    cv_match_percentage: 75,
    ai_enrich_error: null,
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

import { vi } from 'vitest';

export const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
        },
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

export const createDefaultJobMutationsProps = () => ({
    filters: {},
    allJobs: [] as any[],
    selectedJob: { id: 1, title: 'Job 1', ignored: false } as any,
    setSelectedJob: vi.fn(),
    activeTab: 'list' as const,
    autoSelectNext: { current: { shouldSelect: false, previousJobId: null } },
    selectedIds: new Set<number>(),
    setSelectedIds: vi.fn(),
    selectionMode: 'none' as const,
    setSelectionMode: vi.fn(),
});
